from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Category, Drop, Product
from orders.models import ShippingRate


class Command(BaseCommand):
    help = "Create demo categories, products and default shipping rates"

    def handle(self, *args, **opts):
        first = Drop.objects.get_or_create(name="First Drop")[0]
        pink = Drop.objects.get_or_create(name="Pink Oct Drop")[0]
        cats = {n: Category.objects.get_or_create(name=n)[0] for n in ["Dresses", "Tops", "Co-ords", "Outerwear", "Bottoms"]}
        demo = [
            ("Floral Wrap Dress", "NTS-D001", "Dresses", 2400, 12, 3, "Premium label dress"),
            ("Satin Slip Midi", "NTS-D002", "Dresses", 1900, 12, 2, "Satin"),
            ("Linen Co-ord Set", "NTS-C001", "Co-ords", 2200, 12, 2, "Linen blend"),
            ("Ribbed Knit Top", "NTS-T001", "Tops", 900, 5, 4, "Cotton knit"),
            ("Pleated Trousers", "NTS-B001", "Bottoms", 1500, 12, 3, "Crepe"),
            ("Tailored Blazer", "NTS-O001", "Outerwear", 3200, 12, 2, "Wool blend"),
        ]
        for name, sku, cat, price, gst, stock, fabric in demo:
            Product.objects.get_or_create(sku=sku, defaults=dict(
                name=name, category=cats[cat], price=Decimal(price), gst_rate=Decimal(gst),
                stock=stock, drop=first, brand_label="Premium label", condition="New with tags", fabric=fabric, colors="", size_run="",
                mrp=Decimal(price) * 4, description=f"{name} – {fabric}. Limited piece – once it's gone, it's gone.",
                is_featured=True))
        ShippingRate.objects.get_or_create(state="", defaults=dict(base_charge=150, per_kg_charge=45, free_above=25000, eta="4–7 business days"))
        ShippingRate.objects.get_or_create(state="Uttar Pradesh", defaults=dict(base_charge=80, per_kg_charge=25, free_above=15000, eta="2–4 business days"))
        self.stdout.write(self.style.SUCCESS("Demo data created. Add product photos in /admin/."))
