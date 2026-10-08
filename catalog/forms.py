from django import forms

from .models import ContactMessage, Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(choices=[(i, f"{i} ★") for i in range(5, 0, -1)], coerce=int, widget=forms.RadioSelect)

    class Meta:
        model = Review
        fields = ("rating", "title", "body", "image")
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}

    def clean_image(self):
        img = self.cleaned_data.get("image")
        if img and hasattr(img, "size") and img.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Image must be under 5 MB.")
        return img


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
