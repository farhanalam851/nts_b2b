from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.home, name="home"),
    path("manage/", views.manage_home, name="manage_home"),
    path("manage/orders/", views.manage_orders, name="manage_orders"),
    path("manage/orders/<str:number>/", views.manage_order, name="manage_order"),
    path("manage/customers/", views.manage_customers, name="manage_customers"),
]
