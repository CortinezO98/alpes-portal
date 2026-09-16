from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")


SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"],
)

CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=[],
)

FACEBOOK_APP_ID = env("FACEBOOK_APP_ID", default="").strip()
FACEBOOK_APP_SECRET = env("FACEBOOK_APP_SECRET", default="").strip()
FACEBOOK_AUTH_ENABLED = bool(FACEBOOK_APP_ID and FACEBOOK_APP_SECRET)

GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="").strip()
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="").strip()
GOOGLE_AUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

EMAIL_HOST = env("EMAIL_HOST", default="").strip()
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="").strip()
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=15)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="ALPES <no-reply@localhost>")
SERVER_EMAIL = env("SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = "[ALPES] "
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ValueError("EMAIL_USE_TLS y EMAIL_USE_SSL no pueden estar activos al mismo tiempo.")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.google",

    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.portfolio.apps.PortfolioConfig",
    "apps.assessments.apps.AssessmentsConfig",
    "apps.reports.apps.ReportsConfig",
    "apps.audit.apps.AuditConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.accounts.context_processors.social_auth",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


def postgres_database_config():
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="db"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }


DATABASE_ENGINE = env("DATABASE_ENGINE", default="sqlite").strip().lower()

if DATABASE_ENGINE in {"postgres", "postgresql"}:
    DATABASES = {
        "default": postgres_database_config(),
    }
elif DATABASE_ENGINE in {"sqlite", "sqlite3"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ValueError(
        "DATABASE_ENGINE debe ser 'sqlite' o 'postgresql'. "
        f"Valor recibido: {DATABASE_ENGINE!r}"
    )


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_ADAPTER = "apps.accounts.adapters.AlpesAccountAdapter"

SOCIALACCOUNT_ADAPTER = "apps.accounts.adapters.AlpesSocialAccountAdapter"
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "mandatory"
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

SOCIALACCOUNT_PROVIDERS = {
    "facebook": {
        "SCOPE": ["email", "public_profile"],
        "FIELDS": ["id", "email", "name", "first_name", "last_name"],
        "EMAIL_AUTHENTICATION": True,
    },
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
        "EMAIL_AUTHENTICATION": True,
    },
}
if FACEBOOK_AUTH_ENABLED:
    SOCIALACCOUNT_PROVIDERS["facebook"]["APP"] = {
        "client_id": FACEBOOK_APP_ID,
        "secret": FACEBOOK_APP_SECRET,
        "key": "",
    }
if GOOGLE_AUTH_ENABLED:
    SOCIALACCOUNT_PROVIDERS["google"]["APP"] = {
        "client_id": GOOGLE_CLIENT_ID,
        "secret": GOOGLE_CLIENT_SECRET,
        "key": "",
    }


LANGUAGE_CODE = "es-co"

TIME_ZONE = "America/Bogota"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"


LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

PASSWORD_RESET_TIMEOUT = 3600

SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
