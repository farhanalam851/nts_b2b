import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import Address
from catalog.models import Product

from .cart import Cart
from .emails import send_order_email
from .forms import CheckoutForm
from .invoice import build_invoice
from .models import Order, OrderItem
from .pricing import compute_totals


# ---------------------------------------------------------------- cart
def cart_detail(request):
    cart = Cart(request)
    state = ""
    if request.user.is_authenticated:
        addr = request.user.addresses.first()
        state = addr.state if addr else ""
    totals = compute_totals(cart.lines(), state)
    return render(request, "orders/cart.html", {"t": totals, "problems": cart.problems(), "state": state})


@require_POST
def cart_add(request):
    product = get_object_or_404(Product.objects.active(), pk=request.POST.get("product_id"))
    try:
        qty = int(request.POST.get("qty") or 1)
    except ValueError:
        qty = 1
    cart = Cart(request)
    cart.add(product, max(qty, 1))
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect("orders:cart")


@require_POST
def cart_update(request):
    cart = Cart(request)
    for key, val in request.POST.items():
        if key.startswith("qty_"):
            try:
                cart.set(int(key[4:]), int(val))
            except ValueError:
                pass
    return redirect("orders:cart")


@require_POST
def cart_remove(request, pk):
    Cart(request).remove(pk)
    return redirect("orders:cart")


# ---------------------------------------------------------------- checkout
@login_required
def checkout(request):
    cart = Cart(request)
    if not len(cart):
        return redirect("orders:cart")
    addresses = list(request.user.addresses.all())
    if not addresses:
        messages.info(request, "Please add a delivery address first.")
        return redirect(reverse("accounts:address_add") + "?next=" + reverse("orders:checkout"))
    selected = None
    sel_id = request.POST.get("address") or request.GET.get("address")
    if sel_id:
        selected = next((a for a in addresses if str(a.pk) == str(sel_id)), None)
    selected = selected or addresses[0]
    totals = compute_totals(cart.lines(), selected.state)
    form = CheckoutForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        problems = cart.problems()
        if problems:
            for p in problems:
                messages.error(request, p)
            return redirect("orders:cart")
        order = place_order(request, cart, selected, totals, form.cleaned_data)
        if order is None:
            messages.error(request, "Some items just went out of stock. Please review your cart.")
            return redirect("orders:cart")
        send_order_email(order)
        if order.payment_method == "razorpay":
            return redirect("orders:pay", number=order.number)
        messages.success(request, "Order placed. Please complete the bank transfer using the details below.")
        return redirect(order)
    return render(request, "orders/checkout.html", {"t": totals, "addresses": addresses, "selected": selected, "form": form})


@transaction.atomic
def place_order(request, cart, address, totals, data):
    # lock rows and re-check stock
    locked = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=[p.pk for p, _ in cart.lines()])}
    for p, q in cart.lines():
        if locked[p.pk].stock < q:
            transaction.set_rollback(True)
            return None
    u = request.user
    order = Order.objects.create(
        user=u, payment_method=data["payment_method"], notes=data.get("notes", ""),
        ship_name=address.name, ship_phone=address.phone, ship_line1=address.line1, ship_line2=address.line2,
        ship_city=address.city, ship_state=address.state, ship_pincode=address.pincode,
        subtotal=totals["subtotal"], shipping=totals["shipping"], cgst=totals["cgst"], sgst=totals["sgst"],
        igst=totals["igst"], total=totals["total"],
    )
    for row in totals["rows"]:
        p, q = row["product"], row["qty"]
        OrderItem.objects.create(order=order, product=p, name=p.name, sku=p.sku, hsn_code=p.hsn_code,
                                 quantity=q, unit_price=p.price, gst_rate=p.gst_rate, line_total=row["line_total"])
        locked[p.pk].stock -= q
        locked[p.pk].save(update_fields=["stock"])
    cart.clear()
    return order


# ---------------------------------------------------------------- Razorpay
def _rzp_client():
    import razorpay
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
def pay(request, number):
    order = get_object_or_404(Order, number=number, user=request.user)
    if order.payment_status == "paid" or order.payment_method != "razorpay" or order.status == "cancelled":
        return redirect(order)
    if not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET):
        messages.error(request, "Online payments are not configured yet (missing Razorpay keys). Please choose bank transfer or contact us.")
        return redirect(order)
    try:
        if not order.razorpay_order_id:
            rz = _rzp_client().order.create({"amount": order.amount_paise, "currency": settings.CURRENCY_CODE,
                                             "receipt": order.number, "notes": {"order": order.number}})
            order.razorpay_order_id = rz["id"]
            order.save(update_fields=["razorpay_order_id"])
    except Exception as exc:
        messages.error(request, f"Could not start payment: {exc}")
        return redirect(order)
    return render(request, "orders/pay.html", {"order": order, "key_id": settings.RAZORPAY_KEY_ID})


@login_required
@require_POST
def pay_verify(request, number):
    order = get_object_or_404(Order, number=number, user=request.user)
    params = {
        "razorpay_order_id": request.POST.get("razorpay_order_id", ""),
        "razorpay_payment_id": request.POST.get("razorpay_payment_id", ""),
        "razorpay_signature": request.POST.get("razorpay_signature", ""),
    }
    if params["razorpay_order_id"] != order.razorpay_order_id:
        return HttpResponseBadRequest("Order mismatch")
    try:
        _rzp_client().utility.verify_payment_signature(params)
    except Exception:
        order.payment_status = "failed"
        order.save(update_fields=["payment_status"])
        messages.error(request, "Payment verification failed. If money was debited it will be reconciled automatically; contact us with your order number.")
        return redirect(order)
    if order.mark_paid(params["razorpay_payment_id"]):
        send_order_email(order)
    messages.success(request, "Payment received – thank you!")
    return redirect(order)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Set this URL in Razorpay Dashboard -> Webhooks (events: payment.captured, order.paid, payment.failed)."""
    body = request.body.decode()
    sig = request.headers.get("X-Razorpay-Signature", "")
    try:
        _rzp_client().utility.verify_webhook_signature(body, sig, settings.RAZORPAY_WEBHOOK_SECRET)
    except Exception:
        return HttpResponse(status=400)
    event = json.loads(body)
    pay_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    rz_order_id = pay_entity.get("order_id") or event.get("payload", {}).get("order", {}).get("entity", {}).get("id")
    order = Order.objects.filter(razorpay_order_id=rz_order_id).first() if rz_order_id else None
    if order:
        if event.get("event") in ("payment.captured", "order.paid"):
            if order.mark_paid(pay_entity.get("id", "")):
                send_order_email(order)
        elif event.get("event") == "payment.failed" and order.payment_status != "paid":
            order.payment_status = "failed"
            order.save(update_fields=["payment_status"])
    return HttpResponse("ok")


# ---------------------------------------------------------------- orders
@login_required
def order_list(request):
    return render(request, "orders/list.html", {"orders": request.user.orders.all()})


@login_required
def order_detail(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number, user=request.user)
    return render(request, "orders/detail.html", {"order": order, "BANK": settings.BANK_DETAILS})


@login_required
def invoice(request, number):
    order = get_object_or_404(Order, number=number)
    if order.user_id != request.user.id and not request.user.is_staff:
        raise Http404
    try:
        pdf = build_invoice(order)
    except Exception as exc:  # show the reason instead of a blank error page
        messages.error(request, f"Could not generate the invoice: {exc}")
        return redirect(order if order.user_id == request.user.id else "dashboard:manage_order", *([] if order.user_id == request.user.id else [order.number]))
    resp = HttpResponse(pdf, content_type="application/pdf")
    disp = "attachment" if request.GET.get("download") else "inline"
    resp["Content-Disposition"] = f'{disp}; filename="invoice-{order.number}.pdf"'
    return resp
