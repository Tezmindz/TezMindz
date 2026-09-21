"""
Base settings shared by every environment. dev.py and prod.py both
start with `from .base import *` and override only what genuinely
differs (DEBUG, ALLOWED_HOSTS, DATABASES source, security headers).
"""

from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

# settings/base.py -> settings/ -> config/ -> project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = BASE_DIR / "frontend"

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-secret-key-change-in-prod")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "djoser",
    "django_filters",
    "corsheaders",
    # Local apps — see apps/<name>/apps.py for the apps.<name> dotted path
    "apps.accounts",
    "apps.curriculum",
    "apps.games",
    "apps.assessments",
    "apps.gamification",
    "apps.progress",
    "apps.subscriptions",
    "apps.analytics",
    "apps.bulk_import",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Reject oversized request bodies before any view reads them.
    "common.middleware.RequestSizeLimitMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Best-effort abuse signal detection (high 4xx rate, probed tokens, etc.).
    "common.middleware.AbuseMonitoringMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "common.context_processors.gamification_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database -----------------------------------------------------------
# DATABASE_URL drives everything (Render, Docker, or bare Postgres all set
# this the same way). Falls back to local sqlite ONLY when it's unset, so
# a fresh clone can `manage.py migrate` immediately without installing
# Postgres first. Production (prod.py) requires DATABASE_URL to be set —
# it does not fall back.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [FRONTEND_DIR / "static"] if (FRONTEND_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF / JWT / djoser (CONFIRMED stack) --------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.tezmindz_exception_handler",
    # --- Rate limiting --------------------------------------------------
    # Two tiers for authenticated users (burst + sustained) prevent both
    # rapid-fire scripts and prolonged high-volume crawling. Anon IPs get
    # a tighter ceiling. Write endpoints are restricted further.
    "DEFAULT_THROTTLE_CLASSES": [
        "common.throttles.BurstRateThrottle",
        "common.throttles.SustainedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # Authenticated-user tiers
        "burst":       "60/min",   # 1 req/sec average, allows short spikes
        "sustained":   "1000/day", # hard daily ceiling per user/token
        # Anonymous (IP-keyed)
        "anon_burst":  "20/min",   # tighter — no identity verification
        # Auth endpoints (IP-keyed, before identity is established)
        "auth":        "10/min",   # login / token-obtain brute-force guard
        # Specific write endpoints
        "game_submit": "10/min",   # ~1 game per 6s — generous for real play
        "quiz_submit": "10/min",   # same rationale
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

DJOSER = {
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "SEND_ACTIVATION_EMAIL": False,  # revisit once email delivery is configured
    "SERIALIZERS": {},
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:5173", cast=Csv())

# --- Payload size limits ------------------------------------------------
# Hard ceiling applied by RequestSizeLimitMiddleware before any view runs.
# 256 KB is generous for game/quiz JSON payloads; raise only if a specific
# feature genuinely needs bigger bodies (e.g. bulk CSV import).
MAX_REQUEST_BODY_SIZE = config("MAX_REQUEST_BODY_SIZE", default=256 * 1024, cast=int)

# --- Email Configuration ------------------------------------------------
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="smtp.example.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@tezmindz.in")
