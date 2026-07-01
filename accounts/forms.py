from django import forms
from django.contrib.auth.models import User
from .models import Address, UserProfile

class RegistrationForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Phone Number'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password'
    }))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Save the phone number into the profile
            profile = user.profile
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Password'
    }))


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone_number', 'street_address', 'city', 'state', 'postal_code', 'country', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'street_address': forms.TextInput(attrs={'placeholder': 'Street Address'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'placeholder': 'State'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'placeholder': 'Country'}),
            'is_default': forms.CheckboxInput(),
        }
