from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Booking, Seat


class UserRegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name',
            'autocomplete': 'family-name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    username = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a unique username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a secure password (min 6 characters)',
            'autocomplete': 'new-password'
        }),
        min_length=6
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your password',
            'autocomplete': 'new-password'
        }),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match. Please verify and try again.")
        return cleaned_data


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )
    customer_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email for e-ticket delivery'
        })
    )
    customer_phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10-digit mobile number'
        })
    )
    seat_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('SIMULATED_UPI', 'Simulated Instant UPI / QR (Demo)'),
            ('SIMULATED_CARD', 'Simulated Credit / Debit Card (Demo)'),
            ('PAY_AT_COUNTER', 'Pay at Cinema Box Office Counter'),
        ],
        initial='SIMULATED_UPI',
        widget=forms.RadioSelect(attrs={'class': 'payment-radio'})
    )

    def clean_seat_ids(self):
        data = self.cleaned_data.get('seat_ids', '')
        if not data:
            raise forms.ValidationError("No seats were selected.")
        try:
            ids = [int(s.strip()) for s in data.split(',') if s.strip()]
        except ValueError:
            raise forms.ValidationError("Invalid seat selection format.")

        if len(ids) == 0:
            raise forms.ValidationError("Please select at least 1 seat.")
        if len(ids) > 10:
            raise forms.ValidationError("You can book a maximum of 10 seats per transaction.")
        return ids

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '').strip()
        cleaned_phone = "".join(ch for ch in phone if ch.isdigit() or ch == '+')
        if len(cleaned_phone) < 8 or len(cleaned_phone) > 15:
            raise forms.ValidationError("Please provide a valid contact phone number.")
        return cleaned_phone
