from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Q
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    image = models.ImageField(upload_to="categories/", blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return f"{self.parent.name} › {self.name}" if self.parent else self.name

    def save(self, *a, **kw):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*a, **kw)

    def get_absolute_url(self):
        return reverse("catalog:category", args=[self.slug])


class Drop(models.Model):
    """A limited release, e.g. "First Drop", "Pink October Drop"."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    drop_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-drop_date", "-id"]

    def __str__(self):
        return self.name

    def save(self, *a, **kw):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*a, **kw)


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, category__is_active=True)

    def with_rating(self):
        return self.annotate(
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_visible=True)),
            review_count=Count("reviews", filter=Q(reviews__is_visible=True), distinct=True),
        )


class Product(models.Model):
    GST_CHOICES = [(Decimal(x), f"{x}%") for x in (0, 5, 12, 18, 28)]
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    drop = models.ForeignKey(Drop, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    brand_label = models.CharField("Designer / label", max_length=100, blank=True, help_text="e.g. the premium label this piece is from")
    condition = models.CharField(max_length=60, blank=True, default="New with tags")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField("SKU", max_length=40, unique=True)
    description = models.TextField(blank=True)
    fabric = models.CharField(max_length=120, blank=True)
    colors = models.CharField(max_length=200, blank=True, help_text="Comma separated, e.g. Black, Sand, Olive")
    size_run = models.CharField(max_length=100, blank=True, help_text="e.g. S, M, L, XL")
    mrp = models.DecimalField("Retail MRP", max_digits=10, decimal_places=2, null=True, blank=True)
    price = models.DecimalField("Selling price (incl. GST)", max_digits=10, decimal_places=2)
    gst_rate = models.DecimalField("GST %", max_digits=4, decimal_places=1, choices=GST_CHOICES, default=Decimal(12))
    hsn_code = models.CharField("HSN code", max_length=10, default="6109")
    stock = models.PositiveIntegerField(default=0)
    weight_kg = models.DecimalField("Weight / pc (kg)", max_digits=6, decimal_places=3, default=Decimal("0.300"))
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *a, **kw):
        if not self.slug:
            base = slugify(self.name) or "product"
            slug, i = base, 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, i = f"{base}-{i}", i + 1
            self.slug = slug
        super().save(*a, **kw)

    def get_absolute_url(self):
        return reverse("catalog:product", args=[self.slug])

    @property
    def main_image(self):
        img = self.images.first()
        return img.image if img else None

    @property
    def discount_percent(self):
        if self.mrp and self.mrp > self.price:
            return int((1 - self.price / self.mrp) * 100)
        return 0

    @property
    def low_stock(self):
        return 0 < self.stock <= 5

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def color_list(self):
        return [c.strip() for c in self.colors.split(",") if c.strip()]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    image = models.ImageField("Photo (optional)", upload_to="reviews/", blank=True)
    verified = models.BooleanField(default=False, help_text="Reviewer has purchased this product")
    is_visible = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.product} – {self.rating}★ by {self.user}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} – {self.created:%d %b %Y}"
