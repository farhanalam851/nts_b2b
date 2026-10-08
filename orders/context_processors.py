from .cart import Cart


def cart(request):
    return {"cart_count": len(Cart(request)) if hasattr(request, "session") else 0}
