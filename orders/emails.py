from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_order_email(order):
    try:
        body = render_to_string("orders/email.txt", {"order": order, "BANK": settings.BANK_DETAILS,
                                                    "BRAND_NAME": settings.BRAND_NAME, "CUR": settings.CURRENCY_SYMBOL})
        send_mail(f"{settings.BRAND_NAME} – order {order.number}", body, None, [order.user.email], fail_silently=True)
    except Exception:
        pass
