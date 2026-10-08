from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.product_list, name="list"),
    path("category/<slug:slug>/", views.product_list, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product"),
    path("product/<slug:slug>/review/", views.add_review, name="review"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("policy/<slug:slug>/", views.static_page, name="page"),
]
