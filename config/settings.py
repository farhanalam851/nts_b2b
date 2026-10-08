import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=""):
    return os.environ.get(key, default)


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# Render sets this automatically (e.g. my-shop.onrender.com)
RENDER_HOST = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "catalog",
    "orders",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "config.context_processors.brand",
        "orders.context_processors.cart",
    ]},
}]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
if env("DATABASE_URL"):   # Render Postgres
    import dj_database_url
    DATABASES["default"] = dj_database_url.parse(env("DATABASE_URL"), conn_max_age=600)
# For production switch to PostgreSQL, e.g.:
# DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": env("DB_NAME"),
#   "USER": env("DB_USER"), "PASSWORD": env("DB_PASSWORD"), "HOST": env("DB_HOST", "localhost"), "PORT": "5432"}}

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "catalog:home"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT")) if env("MEDIA_ROOT") else BASE_DIR / "media"   # point at a Render disk, e.g. /var/data/media
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Product photos: Cloudinary (free tier, survives redeploys) if CLOUDINARY_URL is set, else local disk.
USE_CLOUDINARY = bool(env("CLOUDINARY_URL"))
if USE_CLOUDINARY:
    INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]
    STORAGES["default"] = {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}

# ---------- Email ----------
if env("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = int(env("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "orders@example.com")

# ---------- Brand / seller details (edit these for the client) ----------
BRAND_NAME = "not this season"
BRAND_TAGLINE = "Curated pieces from brands you love. Premium labels • Limited pieces • 50–90% off retail."
BRAND_INSTAGRAM = "https://www.instagram.com/notthisseason_uae"
SUPPORT_EMAIL = "hello@example.com"
SUPPORT_PHONE = "+971 00 000 0000"
CURRENCY_SYMBOL = "₹"
CURRENCY_CODE = "INR"

SELLER_LEGAL_NAME = "Not This Season"
SELLER_ADDRESS = "Seller address line, City, State, PIN"
SELLER_STATE = "Uttar Pradesh"   # used to decide CGST+SGST (same state) vs IGST (other state)
SELLER_GSTIN = "00AAAAA0000A1Z5"
SHIPPING_GST_RATE = 18           # % GST charged on freight

BANK_DETAILS = "Account name: Not This Season\nBank: XXXX Bank\nA/C: 0000000000\nIFSC: XXXX0000000"

# ---------- Developer credit (shown in footer) ----------
DEVELOPER_NAME = "webby_farhan"
DEVELOPER_TITLE = "Website Development"
DEVELOPER_INSTAGRAM = "https://www.instagram.com/webby_farhan"
DEVELOPER_INSTAGRAM_HANDLE = "@webby_farhan"
DEVELOPER_EMAIL = "farhanalam8510@gmail.com"

# ---------- Razorpay ----------
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET")

if not DEBUG:
    SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_REDIRECT_EXEMPT = [r"^healthz/?$"]
