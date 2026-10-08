from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse

from catalog.models import Product


class ShippingRate(models.Model):
    """Freight rule per destination state. A row with blank state is the default for all other states."""
    state = models.CharField(max_length=60, blank=True, unique=True, help_text="Leave blank for the default rate")
    base_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("150"))
    per_kg_charge = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("40"))
    free_above = models.DecimalField("Free shipping above (subtotal)", max_digits=10, decimal_places=2, null=True, blank=True)
    eta = models.CharField("Delivery estimate", max_length=50, default="4–7 business days")

    def __str__(self):
        return self.state or "Default (all other states)"


class Order(models.Model):
    STATUS = [("pending", "Pending"), ("confirmed", "Confirmed"), ("processing", "Processing"),
              ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled")]
    PAY_STATUS = [("unpaid", "Unpaid"), ("paid", "Paid"), ("failed", "Failed"), ("refunded", "Refunded")]
    PAY_METHOD = [("razorpay", "Online (UPI / Card / Netbanking)"), ("bank", "Bank transfer (NEFT/RTGS)")]

    number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=12, choices=STATUS, default="pending")
    payment_method = models.CharField(max_length=10, choices=PAY_METHOD)
    payment_status = models.CharField(max_length=10, choices=PAY_STATUS, default="unpaid")
    razorpay_order_id = models.CharField(max_length=60, blank=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=60, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    ship_name = models.CharField(max_length=100)
    ship_phone = models.CharField(max_length=20)
    ship_line1 = models.CharField(max_length=200)
    ship_line2 = models.CharField(max_length=200, blank=True)
    ship_city = models.CharField(max_length=80)
    ship_state = models.CharField(max_length=60)
    ship_pincode = models.CharField(max_length=6)
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField("Items total (incl. GST)", max_digits=12, decimal_places=2)
    shipping = models.DecimalField("Delivery (incl. GST)", max_digits=10, decimal_places=2, default=0)
    cgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    courier = models.CharField(max_length=60, blank=True)
    tracking_number = models.CharField(max_length=80, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.number or f"Order #{self.pk}"

    def save(self, *a, **kw):
        super().save(*a, **kw)
        if not self.number:
            self.number = f"NTS-{self.pk:06d}"
            super().save(update_fields=["number"])

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.number])

    @property
    def tax_total(self):
        return self.cgst + self.sgst + self.igst

    @property
    def is_intra_state(self):
        return self.igst == 0

    @property
    def amount_paise(self):
        return int((self.total * 100).to_integral_value())

    @transaction.atomic
    def mark_paid(self, payment_id=""):
        from django.utils import timezone
        order = Order.objects.select_for_update().get(pk=self.pk)
        if order.payment_status == "paid":
            return False
        order.payment_status = "paid"
        order.paid_at = timezone.now()
        if payment_id:
            order.razorpay_payment_id = payment_id
        if order.status == "pending":
            order.status = "confirmed"
        order.save()
        self.__dict__.update(order.__dict__)
        return True

    @transaction.atomic
    def cancel(self):
        """Cancel and put stock back."""
        order = Order.objects.select_for_update().get(pk=self.pk)
        if order.status == "cancelled":
            return
        for item in order.items.select_related("product"):
            if item.product_id:
                Product.objects.filter(pk=item.product_id).update(stock=models.F("stock") + item.quantity)
        order.status = "cancelled"
        order.save()
        self.__dict__.update(order.__dict__)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=40)
    hsn_code = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_rate = models.DecimalField(max_digits=4, decimal_places=1)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)   # excl. GST

    def __str__(self):
        return f"{self.quantity} × {self.name}"
