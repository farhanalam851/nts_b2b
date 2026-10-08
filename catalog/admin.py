from django.contrib import admin

from .models import Category, Drop, ContactMessage, Product, ProductImage, Review


@admin.register(Drop)
class DropAdmin(admin.ModelAdmin):
    list_display = ("name", "drop_date", "is_active")
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand_label", "sku", "category", "drop", "price", "gst_rate", "stock", "is_active", "is_featured")
    list_filter = ("category", "drop", "is_active", "is_featured", "gst_rate")
    list_editable = ("price", "stock", "is_active", "is_featured")
    search_fields = ("name", "sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "verified", "is_visible", "created")
    list_filter = ("rating", "verified", "is_visible")
    list_editable = ("is_visible",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created", "handled")
    list_editable = ("handled",)
