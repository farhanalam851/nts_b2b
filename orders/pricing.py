"""Retail pricing: all prices are GST-inclusive. We extract the GST portion and split it CGST+SGST vs IGST for the invoice."""
import math
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

from .models import ShippingRate

CENT = Decimal("0.01")


def money(x):
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


def get_shipping_rate(state):
    return (ShippingRate.objects.filter(state=state).first()
            or ShippingRate.objects.filter(state="").first())


def compute_totals(lines, state):
    """lines: iterable of (product, qty). state: destination state name (may be '')."""
    intra = bool(state) and state.strip().lower() == settings.SELLER_STATE.strip().lower()
    subtotal = Decimal("0")   # gross, GST included
    tax = Decimal("0")        # GST contained in the gross
    weight = Decimal("0")
    rows = []
    for product, qty in lines:
        line = money(product.price * qty)
        gst = money(line - line / (1 + product.gst_rate / 100))
        subtotal += line
        tax += gst
        weight += product.weight_kg * qty
        rows.append({"product": product, "qty": qty, "line_total": line, "gst": gst})

    rate = get_shipping_rate(state)
    shipping = Decimal("0")
    eta = ""
    if rate:
        eta = rate.eta
        if not (rate.free_above and subtotal >= rate.free_above):
            shipping = money(rate.base_charge + rate.per_kg_charge * max(1, math.ceil(weight)))
    if subtotal == 0:
        shipping = Decimal("0")
    ship_rate = Decimal(settings.SHIPPING_GST_RATE)
    tax += money(shipping - shipping / (1 + ship_rate / 100))

    if intra:
        cgst = money(tax / 2)
        sgst = tax - cgst
        igst = Decimal("0")
    else:
        cgst = sgst = Decimal("0")
        igst = tax
    return {
        "rows": rows, "subtotal": subtotal, "shipping": shipping, "cgst": cgst, "sgst": sgst, "igst": igst,
        "tax_total": cgst + sgst + igst, "total": subtotal + shipping, "weight": weight,
        "intra": intra, "eta": eta, "free_above": rate.free_above if rate else None,
    }
