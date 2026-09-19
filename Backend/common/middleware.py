"""
Security middleware for TezMindz.

RequestSizeLimitMiddleware
--------------------------
Rejects incoming requests whose Content-Length exceeds MAX_REQUEST_BODY_SIZE
(default: 256 KB, configurable in settings) before the view layer ever reads
the body. This prevents memory exhaustion / slow-drain attacks.

Only applied to mutating HTTP methods (POST/PUT/PATCH) because GET/HEAD/DELETE
bodies are meaningless by convention and zero-size in practice.

AbuseMonitoringMiddleware
-------------------------
Best-effort, append-only abuse signal writer. Writes to analytics.Event
(which already exists, has the right indexes, and is designed for exactly
this kind of best-effort append). A logging failure here must never fail the
actual request — the outer try/except guarantees that.

Patterns flagged
~~~~~~~~~~~~~~~~
* >30 4xx responses from the same IP within a rolling window (tracked in the
  Django cache, no extra model needed).
* Any 401 to a path that already has a Bearer token header (token rejected /
  expired — might indicate token theft probing).
* POST to write endpoints with anomalously large payloads (even after the
  size limit, anything >16 KB is noteworthy for game/quiz submissions).
"""

import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

logger = logging.getLogger("tezmindz.security")

# ---------------------------------------------------------------------------
# Configurable constants (override in settings)
# ---------------------------------------------------------------------------

# Hard ceiling on request body size for mutating methods (bytes).
_DEFAULT_MAX_BODY = 256 * 1024  # 256 KB

# 4xx threshold: number of 4xx responses from one IP in _ABUSE_WINDOW_SECS
# before an abuse event is logged.
_ABUSE_4XX_THRESHOLD = 30
_ABUSE_WINDOW_SECS = 60  # rolling 1-minute window
_LARGE_PAYLOAD_BYTES = 16 * 1024  # 16 KB noteworthy for game/quiz payloads


# ---------------------------------------------------------------------------
# 1. Request-size gate
# ---------------------------------------------------------------------------

class RequestSizeLimitMiddleware:
    """
    Reject oversized request bodies before the view reads request.body.

    Only mutating methods are checked. Content-Length is used when present
    (it's cheap). If absent (chunked transfer encoding), the middleware is
    bypassed — the view layer's json.loads() will still handle the data,
    but true chunked upload attacks are an infrastructure-layer concern
    (nginx/gunicorn limits).
    """

    MUTATING_METHODS = {"POST", "PUT", "PATCH"}

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_body = getattr(settings, "MAX_REQUEST_BODY_SIZE", _DEFAULT_MAX_BODY)
        self.admin_max_body = getattr(settings, "MAX_ADMIN_UPLOAD_SIZE", 15 * 1024 * 1024)

    def __call__(self, request):
        if request.method in self.MUTATING_METHODS:
            content_length = request.META.get("CONTENT_LENGTH")
            if content_length:
                try:
                    length = int(content_length)
                except (ValueError, TypeError):
                    length = 0
                current_limit = self.admin_max_body if request.path.startswith("/admin/") else self.max_body
                if length > current_limit:
                    logger.warning(
                        "RequestSizeLimitMiddleware: rejected %s %s — "
                        "Content-Length %d > limit %d (IP: %s)",
                        request.method,
                        request.path,
                        length,
                        current_limit,
                        _get_client_ip(request),
                    )
                    return HttpResponse(
                        '{"success":false,"error":{"code":"PAYLOAD_TOO_LARGE",'
                        '"message":"Request body exceeds the maximum allowed size."}}',
                        status=413,
                        content_type="application/json",
                    )
        return self.get_response(request)


# ---------------------------------------------------------------------------
# 2. Abuse / anomaly monitoring
# ---------------------------------------------------------------------------

class AbuseMonitoringMiddleware:
    """
    Post-response middleware that tracks suspicious signals and logs them to
    analytics.Event best-effort. Never raises — a logging failure must not
    block the response.

    This middleware intentionally does NOT block requests. It is a detection
    layer, not an enforcement layer. Enforcement is the throttle layer's job.
    """

    # Paths considered write-sensitive (prefix match)
    WRITE_PATHS = ("/api/game/", "/api/games/", "/api/quiz/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._inspect(request, response)
        except Exception:  # noqa: BLE001 — best-effort; never fail the request
            logger.exception("AbuseMonitoringMiddleware: unexpected error during inspection")
        return response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _inspect(self, request, response):
        ip = _get_client_ip(request)
        status = response.status_code

        # 1. Track 4xx rate per IP using Django cache (no extra model)
        if 400 <= status < 500:
            cache_key = f"abuse:4xx:{ip}"
            count = cache.get(cache_key, 0) + 1
            cache.set(cache_key, count, timeout=_ABUSE_WINDOW_SECS)
            if count >= _ABUSE_4XX_THRESHOLD:
                self._log_event(
                    ip=ip,
                    event_subtype="high_4xx_rate",
                    payload={
                        "ip": ip,
                        "count": count,
                        "window_secs": _ABUSE_WINDOW_SECS,
                        "last_path": request.path,
                        "status": status,
                    },
                )
                # Reset counter so we log once per window, not every subsequent request
                cache.set(cache_key, 0, timeout=_ABUSE_WINDOW_SECS)

        # 2. 401 on a request that already carried a Bearer token → token probing
        if status == 401 and "HTTP_AUTHORIZATION" in request.META:
            auth_header = request.META["HTTP_AUTHORIZATION"]
            if auth_header.startswith("Bearer "):
                self._log_event(
                    ip=ip,
                    event_subtype="rejected_bearer_token",
                    payload={
                        "ip": ip,
                        "path": request.path,
                        "method": request.method,
                    },
                )

        # 3. Anomalously large write payloads on game/quiz endpoints
        if request.method == "POST" and any(request.path.startswith(p) for p in self.WRITE_PATHS):
            content_length = request.META.get("CONTENT_LENGTH")
            if content_length:
                try:
                    length = int(content_length)
                except (ValueError, TypeError):
                    length = 0
                if length > _LARGE_PAYLOAD_BYTES:
                    self._log_event(
                        ip=ip,
                        event_subtype="large_write_payload",
                        payload={
                            "ip": ip,
                            "path": request.path,
                            "content_length": length,
                            "threshold": _LARGE_PAYLOAD_BYTES,
                        },
                    )

    @staticmethod
    def _log_event(ip: str, event_subtype: str, payload: dict):
        """
        Write to analytics.Event best-effort. We reuse the existing model
        and its indexes rather than adding a new table.

        analytics.Event.EventType does not have an ABUSE entry — we store
        as a sentinel value in payload["subtype"] and use a special
        event_type string that sorts into the existing indexes cleanly.
        The payload dict carries the structured detail.
        """
        try:
            from apps.analytics.models import Event  # local import avoids circular at module load

            logger.warning(
                "ABUSE_SIGNAL ip=%s subtype=%s payload=%s",
                ip,
                event_subtype,
                payload,
            )
            # analytics.Event uses TextChoices — store using a raw value
            # that doesn't match any existing choice so it's easy to filter
            # on in the admin ("security_alert"). We write via the ORM
            # directly, bypassing validation, because:
            # (a) the field is just a CharField with choices — it won't
            #     raise a DB-level error for an unknown value.
            # (b) We want monitoring to survive even if Event.EventType
            #     hasn't been updated yet.
            Event.objects.create(
                student=None,
                event_type="security_alert",
                payload={"subtype": event_subtype, "ip": ip, **payload},
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "AbuseMonitoringMiddleware._log_event: failed to write Event for ip=%s subtype=%s",
                ip,
                event_subtype,
            )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _get_client_ip(request) -> str:
    """
    Return the real client IP, honouring X-Forwarded-For when set by a
    trusted proxy (Render, Heroku, nginx). We take only the first address in
    the chain — intermediate proxies append their own IP after it.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")
