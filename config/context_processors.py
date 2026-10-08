from django.conf import settings


def brand(request):
    return {
        "BRAND_NAME": settings.BRAND_NAME,
        "BRAND_TAGLINE": settings.BRAND_TAGLINE,
        "BRAND_INSTAGRAM": settings.BRAND_INSTAGRAM,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "SUPPORT_PHONE": settings.SUPPORT_PHONE,
        "CUR": settings.CURRENCY_SYMBOL,
        "DEV_NAME": settings.DEVELOPER_NAME,
        "DEV_TITLE": settings.DEVELOPER_TITLE,
        "DEV_INSTAGRAM": settings.DEVELOPER_INSTAGRAM,
        "DEV_HANDLE": settings.DEVELOPER_INSTAGRAM_HANDLE,
        "DEV_EMAIL": settings.DEVELOPER_EMAIL,
    }
