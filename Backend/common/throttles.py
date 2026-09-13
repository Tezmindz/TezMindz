"""
Rate-limiting throttle classes used across every data-bearing API.

Design decisions
----------------
* Two tiers per authenticated user: burst (short window) + sustained
  (longer window). Both must pass for a request to proceed. This catches
  both rapid scripted hammering and high-volume sustained crawling.
* Anonymous requests are throttled by IP only, at tighter limits.
* Write endpoints (game submit, quiz submit, auth) get dedicated
  throttle classes so we can tighten them independently without touching
  the read-path limits.
* Rates live in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] so
  they're env-overridable without a code change.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


# ---------------------------------------------------------------------------
# Generic tiers — applied to all authenticated read endpoints
# ---------------------------------------------------------------------------

class BurstRateThrottle(UserRateThrottle):
    """
    Short-window limit: prevents rapid-fire bursts from a single user/token.
    Scope key must match REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['burst'].
    """
    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """
    Long-window (day) limit: prevents high-volume sustained scraping even
    when individual bursts stay below the burst limit.
    Scope key must match REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['sustained'].
    """
    scope = "sustained"


class AnonBurstThrottle(AnonRateThrottle):
    """
    Unauthenticated requests are throttled by IP at a tighter burst limit.
    """
    scope = "anon_burst"


# ---------------------------------------------------------------------------
# Write-endpoint specific throttles (tighter limits)
# ---------------------------------------------------------------------------

class AuthEndpointThrottle(AnonRateThrottle):
    """
    Applied to login/token endpoints (already enforced by djoser/simplejwt
    views + can be added to common.views login_page).
    Throttled by IP — user identity isn't known yet at auth time.
    """
    scope = "auth"


class GameSubmitThrottle(UserRateThrottle):
    """
    Applied to the game-session submit endpoint.
    Tighter than the generic burst limit to prevent XP/coin farming via
    rapid repeated submissions. A real student can't physically complete
    a game faster than ~30 s, so 10/min is generous.
    """
    scope = "game_submit"


class QuizSubmitThrottle(UserRateThrottle):
    """
    Applied to the quiz-attempt submit endpoint.
    Same rationale as GameSubmitThrottle — prevents answer-farming.
    """
    scope = "quiz_submit"
