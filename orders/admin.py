from django.contrib import admin

from .models import Order, OrderItem, ShippingRate


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "name", "sku", "hsn_code", "quantity", "unit_price", "gst_rate", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "ship_state", "total", "payment_method", "payment_status", "status", "created")
    list_filter = ("status", "payment_status", "payment_method", "ship_state")
    search_fields = ("number", "user__email", "razorpay_payment_id")
    list_editable = ("status", "payment_status")
    inlines = [OrderItemInline]
    readonly_fields = ("number", "razorpay_order_id", "razorpay_payment_id", "paid_at")
    actions = ["mark_paid", "cancel_orders"]

    @admin.action(description="Mark selected as PAID (bank transfer received)")
    def mark_paid(self, request, qs):
        for o in qs:
            o.mark_paid()

    @admin.action(description="Cancel selected & restock")
    def cancel_orders(self, request, qs):
        for o in qs:
            o.cancel()


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ("__str__", "base_charge", "per_kg_charge", "free_above", "eta")
