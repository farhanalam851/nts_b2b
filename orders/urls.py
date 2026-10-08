from django.urls import path

from . import views

app_name = "orders"
urlpatterns = [
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("webhook/razorpay/", views.razorpay_webhook, name="webhook"),
    path("", views.order_list, name="list"),
    path("<str:number>/", views.order_detail, name="detail"),
    path("<str:number>/pay/", views.pay, name="pay"),
    path("<str:number>/verify/", views.pay_verify, name="verify"),
    path("<str:number>/invoice/", views.invoice, name="invoice"),
]
