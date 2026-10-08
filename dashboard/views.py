from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from catalog.models import Product, Review
from orders.models import Order

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="accounts:login")


@login_required
def home(request):
    orders = request.user.orders.all()
    paid = orders.exclude(status="cancelled")
    return render(request, "dashboard/home.html", {
        "recent": orders[:5],
        "order_count": orders.count(),
        "open_count": orders.exclude(status__in=["delivered", "cancelled"]).count(),
        "spent": paid.filter(payment_status="paid").aggregate(s=Sum("total"))["s"] or 0,
        "unpaid": paid.filter(payment_status="unpaid").count(),
    })


@staff_required
def manage_home(request):
    today = timezone.now()
    since = today - timedelta(days=30)
    paid = Order.objects.filter(payment_status="paid").exclude(status="cancelled")
    daily = (paid.filter(created__gte=since).annotate(d=TruncDate("created"))
             .values("d").annotate(total=Sum("total"), n=Count("id")).order_by("-d")[:14])
    return render(request, "dashboard/manage_home.html", {
        "revenue_30": paid.filter(created__gte=since).aggregate(s=Sum("total"))["s"] or 0,
        "revenue_all": paid.aggregate(s=Sum("total"))["s"] or 0,
        "orders_pending": Order.objects.filter(status__in=["pending", "confirmed", "processing"]).count(),
        "unpaid_bank": Order.objects.filter(payment_method="bank", payment_status="unpaid").exclude(status="cancelled").count(),
        "customers_n": User.objects.filter(is_staff=False).count(),
        "reviews_n": Review.objects.count(),
        "daily": daily,
        "recent": Order.objects.select_related("user")[:8],
        "low_stock": Product.objects.filter(is_active=True, stock__lte=2).order_by("stock")[:10],
        "top": (Product.objects.filter(orderitem__order__payment_status="paid")
                .annotate(units=Sum("orderitem__quantity")).order_by("-units")[:5]),
    })


@staff_required
def manage_orders(request):
    qs = Order.objects.select_related("user")
    status, pay = request.GET.get("status", ""), request.GET.get("payment", "")
    q = request.GET.get("q", "").strip()
    if status:
        qs = qs.filter(status=status)
    if pay:
        qs = qs.filter(payment_status=pay)
    if q:
        qs = qs.filter(number__icontains=q) | qs.filter(user__first_name__icontains=q) | qs.filter(user__email__icontains=q)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "dashboard/manage_orders.html", {
        "page": page, "statuses": Order.STATUS, "pays": Order.PAY_STATUS, "status": status, "pay": pay, "q": q})


@staff_required
def manage_order(request, number):
    order = get_object_or_404(Order, number=number)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "mark_paid":
            order.mark_paid()
            messages.success(request, "Marked as paid.")
        elif action == "cancel":
            order.cancel()
            messages.info(request, "Order cancelled and stock restored.")
        else:
            st = request.POST.get("status")
            if st in dict(Order.STATUS):
                order.status = st
            order.courier = request.POST.get("courier", "")[:60]
            order.tracking_number = request.POST.get("tracking_number", "")[:80]
            order.save()
            messages.success(request, "Order updated.")
        return redirect("dashboard:manage_order", number=number)
    return render(request, "dashboard/manage_order.html", {"order": order, "statuses": Order.STATUS})


@staff_required
def manage_customers(request):
    return render(request, "dashboard/manage_customers.html", {
        "buyers": User.objects.filter(is_staff=False).annotate(order_count=Count("orders")).order_by("-date_joined")})

