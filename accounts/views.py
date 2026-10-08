from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import AddressForm, ProfileForm, RegisterForm
from .models import Address


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome! Your account is ready.")
        return redirect("dashboard:home")
    return render(request, "accounts/form.html", {"form": form, "title": "Create an account",
                                                  "button": "Register", "alt": "login"})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form, "addresses": request.user.addresses.all()})


@login_required
def address_form(request, pk=None):
    instance = get_object_or_404(Address, pk=pk, user=request.user) if pk else None
    form = AddressForm(request.POST or None, instance=instance)
    nxt = request.GET.get("next") or request.POST.get("next") or ""
    if request.method == "POST" and form.is_valid():
        addr = form.save(commit=False)
        addr.user = request.user
        if not request.user.addresses.exists():
            addr.is_default = True
        addr.save()
        messages.success(request, "Address saved.")
        if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
            return redirect(nxt)
        return redirect("accounts:profile")
    return render(request, "accounts/form.html", {"form": form, "title": "Delivery address", "button": "Save address", "next": nxt})


@login_required
def address_delete(request, pk):
    if request.method == "POST":
        get_object_or_404(Address, pk=pk, user=request.user).delete()
        messages.info(request, "Address removed.")
    return redirect("accounts:profile")
