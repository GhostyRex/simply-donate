from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import PaymentMethod, GiftDonation

# PayPal imports.
from paypal.standard.forms import PayPalPaymentsForm

# Country import.
# from django_countries.data import COUNTRIES


class CustomPayPalPaymentsForm(PayPalPaymentsForm):
    @staticmethod
    def get_html_submit_element():
        return """<button type="submit">Continue on PayPal website</button>"""


class UserRegistrationForm(UserCreationForm):
    show = forms.BooleanField(label="Show Password", required=False)

    phone = forms.CharField(label='phone', required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password1', 'password2', 'phone', 'show'
        ]

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)

        for field_name in [
            'username', 'email', 'password1', 'password2', 'phone'
        ]:
            self.fields[field_name].help_text = None
            self.fields[field_name].widget = forms.TextInput(attrs={'autocomplete': 'off'})

        # Change password type to text show the password is hidden.
        self.fields['password1'].widget = forms.TextInput(attrs={'type': 'password'})
        self.fields['password2'].widget = forms.TextInput(attrs={'type': 'password'})

        self.fields['phone'].widget = forms.TextInput(attrs={'placeholder': '+1-234-567-8999'})
        self.fields['email'].required = True


class MoneyDonationForm(forms.Form):
    amount = forms.DecimalField(
        label='Amount ($)', required=True, max_digits=64, decimal_places=2,
        widget=forms.TextInput(attrs={'placeholder': '20.00', 'autocomplete': 'off'})
    )

    # Payment_method.
    payment_method = forms.ModelChoiceField(
        label='Payment Method', required=True, queryset=PaymentMethod.objects.filter()
    )


class GiftDonationForm(forms.ModelForm):
    # Contact.
    contact = forms.CharField(
        label='Phone Number', required=True,
        widget=forms.TextInput(attrs={'placeholder': '+1-301-244-5756', 'autocomplete': 'off'})
    )

    # Address_one.
    street = forms.CharField(
        label='Street', required=True, widget=forms.TextInput(attrs={'autocomplete': 'off'}), max_length=300
    )

    # City.
    city = forms.CharField(
        label='City', required=True, widget=forms.TextInput(attrs={'autocomplete': 'off'}), max_length=300
    )

    # State.
    # state = models.CharField(max_length=200, null=True, blank=True)

    # ZipCode.
    zipcode = forms.CharField(
        label='ZipCode', required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}), max_length=300
    )

    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"rows": 7, "cols": 40}),
        label="Gift Description",
    )

    class Meta:
        model = GiftDonation

        fields = ['contact', 'street', 'city', 'zipcode', 'description', 'image']


class ContactUsForm(forms.Form):
    name = forms.CharField(required=True, widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    subject = forms.CharField(required=True, widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"rows": 7, "cols": 40, 'autocomplete': 'off'}),
        label="Your Message",
        max_length=1000
    )

    # attach = forms.FileField(required=False, label='Attachment', widget=forms.ClearableFileInput(attrs={'multiple': True}))
