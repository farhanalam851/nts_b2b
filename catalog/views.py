from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ContactForm, ReviewForm
from .models import Category, Drop, Product, Review


def home(request):
    products = Product.objects.active().with_rating().prefetch_related("images")
    return render(request, "catalog/home.html", {
        "categories": Category.objects.filter(is_active=True, parent__isnull=True)[:8],
        "drops": Drop.objects.filter(is_active=True)[:5],
        "featured": products.filter(is_featured=True)[:8],
        "latest": products[:8],
    })


def product_list(request, slug=None):
    category = None
    qs = Product.objects.active().with_rating().prefetch_related("images")
    if slug:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        ids = [category.pk] + list(category.children.values_list("pk", flat=True))
        qs = qs.filter(category_id__in=ids)
    drop = None
    if request.GET.get("drop"):
        drop = Drop.objects.filter(slug=request.GET["drop"], is_active=True).first()
        if drop:
            qs = qs.filter(drop=drop)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(brand_label__icontains=q) | Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q) | Q(fabric__icontains=q))
    for key, lookup in (("min", "price__gte"), ("max", "price__lte")):
        try:
            val = request.GET.get(key)
            if val:
                qs = qs.filter(**{lookup: float(val)})
        except ValueError:
            pass
    sort = request.GET.get("sort", "new")
    qs = qs.order_by({"new": "-created", "price_asc": "price", "price_desc": "-price",
                      "rating": "-avg_rating"}.get(sort, "-created"), "-id")
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "catalog/product_list.html", {
        "page": page, "category": category, "drop": drop, "drops": Drop.objects.filter(is_active=True), "q": q, "sort": sort, "qs_params": params.urlencode(),
        "categories": Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children"),
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.active().prefetch_related("images"), slug=slug)
    reviews = product.reviews.filter(is_visible=True).select_related("user")
    stats = reviews.aggregate(avg=Avg("rating"), n=Count("id"))
    breakdown = {i: reviews.filter(rating=i).count() for i in range(5, 0, -1)}
    my_review = reviews.filter(user=request.user).first() if request.user.is_authenticated else None
    related = Product.objects.active().with_rating().filter(category=product.category).exclude(pk=product.pk)[:4]
    return render(request, "catalog/product_detail.html", {
        "product": product, "reviews": reviews, "stats": stats, "breakdown": breakdown,
        "form": ReviewForm(instance=my_review), "my_review": my_review, "related": related,
    })


@login_required
@require_POST
def add_review(request, slug):
    from orders.models import OrderItem
    product = get_object_or_404(Product, slug=slug)
    existing = Review.objects.filter(product=product, user=request.user).first()
    form = ReviewForm(request.POST, request.FILES, instance=existing)
    if form.is_valid():
        review = form.save(commit=False)
        review.product, review.user = product, request.user
        review.verified = OrderItem.objects.filter(
            order__user=request.user, product=product, order__payment_status="paid").exists()
        review.save()
        messages.success(request, "Thanks – your review has been saved.")
    else:
        messages.error(request, "Please correct the review form: " + "; ".join(
            f"{k}: {', '.join(v)}" for k, v in form.errors.items()))
    return redirect(product.get_absolute_url() + "#reviews")


PAGES = {
    "shipping-returns": ("Shipping & Returns", [
        "Orders are dispatched within 2–4 business days after payment confirmation.",
        "Delivery charges are calculated from your state and order weight and include GST. Free shipping applies above the threshold shown at checkout.",
        "Claims for damaged or incorrect goods must be raised within 48 hours of delivery with photos. Please check the shipping & returns terms agreed with your seller for other returns.",
    ]),
    "how-drops-work": ("how our drops work", [
        "Pieces are released in limited drops. Each style is one-of-a-kind or available in very small quantities.",
        "Create an account, then shop the drop when it opens. Once a piece is gone it is gone.",
        "Every piece is authentic, from premium labels, at 50–90% off retail.",
    ]),
    "terms": ("Terms of Sale", [
        "All prices are inclusive of GST. The GST amount is shown on your invoice.",
        "Each piece is limited; stock is reserved when you place your order.",
        "Colours may vary slightly from photographs.",
    ]),
    "privacy": ("Privacy Policy", [
        "We collect only the business and contact details needed to process orders and invoices.",
        "Payments are handled by Razorpay; we do not store card details.",
    ]),
}


def static_page(request, slug):
    if slug not in PAGES:
        raise Http404
    title, paras = PAGES[slug]
    return render(request, "catalog/page.html", {"title": title, "paras": paras})


def about(request):
    return render(request, "catalog/about.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        msg = form.save()
        try:
            mail_admins(f"New enquiry from {msg.name}", f"{msg.email} / {msg.phone}\n\n{msg.message}", fail_silently=True)
        except Exception:
            pass
        messages.success(request, "Thanks! We'll get back to you shortly.")
        return redirect("catalog:contact")
    return render(request, "catalog/contact.html", {"form": form})
