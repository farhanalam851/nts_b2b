from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Address, User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        for f in ("first_name", "phone"):
            self.fields[f].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone")


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ("user",)
