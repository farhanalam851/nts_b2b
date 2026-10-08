from django import forms

from .models import Order


class CheckoutForm(forms.Form):
    payment_method = forms.ChoiceField(choices=Order.PAY_METHOD, widget=forms.RadioSelect, initial="razorpay")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Order notes (optional)")
