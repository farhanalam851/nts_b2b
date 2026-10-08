from catalog.models import Product


class Cart:
    KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        self.data = self.session.setdefault(self.KEY, {})

    def _save(self):
        self.session.modified = True

    def add(self, product, qty):
        self.data[str(product.pk)] = self.data.get(str(product.pk), 0) + int(qty)
        self._save()

    def set(self, product_id, qty):
        if qty <= 0:
            self.data.pop(str(product_id), None)
        else:
            self.data[str(product_id)] = int(qty)
        self._save()

    def remove(self, product_id):
        self.data.pop(str(product_id), None)
        self._save()

    def clear(self):
        self.session[self.KEY] = {}
        self._save()

    def __len__(self):
        return sum(self.data.values())

    def lines(self):
        products = Product.objects.active().prefetch_related("images").in_bulk([int(k) for k in self.data])
        return [(products[int(k)], q) for k, q in self.data.items() if int(k) in products]

    def problems(self):
        out = []
        for p, q in self.lines():
            if q > p.stock:
                out.append(f"{p.name}: only {p.stock} pcs in stock.")
        return out
