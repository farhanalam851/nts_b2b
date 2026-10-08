from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "accounts"


def tpl(cls, **kw):
    return cls.as_view(template_name="accounts/form.html", **kw)


urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/form.html",
         extra_context={"title": "Log in", "button": "Log in", "alt": "register"}), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),   # POST only (Django 5)
    path("profile/", views.profile, name="profile"),
    path("address/add/", views.address_form, name="address_add"),
    path("address/<int:pk>/edit/", views.address_form, name="address_edit"),
    path("address/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("password/change/", tpl(auth_views.PasswordChangeView, success_url=reverse_lazy("accounts:profile"),
         extra_context={"title": "Change password", "button": "Update"}), name="password_change"),
    path("password/reset/", tpl(auth_views.PasswordResetView, email_template_name="registration/reset_email.txt",
         success_url=reverse_lazy("accounts:password_reset_done"),
         extra_context={"title": "Reset password", "button": "Send reset link"}), name="password_reset"),
    path("password/reset/sent/", auth_views.PasswordResetDoneView.as_view(template_name="accounts/message.html",
         extra_context={"title": "Check your email", "text": "If that address has an account, a reset link is on its way."}),
         name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", tpl(auth_views.PasswordResetConfirmView,
         success_url=reverse_lazy("accounts:password_reset_complete"),
         extra_context={"title": "Choose a new password", "button": "Save password"}), name="password_reset_confirm"),
    path("password/reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="accounts/message.html",
         extra_context={"title": "Password updated", "text": "You can now log in with your new password."}),
         name="password_reset_complete"),
]
