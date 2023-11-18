from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from user.models import User
from django.contrib.auth import authenticate


class CustomAuthenticationForm(forms.Form):
    username_or_email = forms.CharField(max_length=254, required=True, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username_or_email')
        password = cleaned_data.get('password')

        if username_or_email and password:
            # Check if the input is an email address
            if '@' in username_or_email:
                # If it's an email, try to get the user by email
                try:
                    user = User.objects.get(email=username_or_email)
                    cleaned_data['username'] = user.username
                except User.DoesNotExist:
                    self.add_error('username_or_email', 'Invalid login credentials')
            else:
                # If it's not an email, assume it's a username
                cleaned_data['username'] = username_or_email

            # Authenticate using either username or email
            user = authenticate(username=cleaned_data['username'], password=password)
            if user is None:
                self.add_error('username_or_email', 'Invalid login credentials')
            elif not user.is_active:
                self.add_error('username_or_email', 'User account is not active')

        return cleaned_data

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UpstoxForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['upstox_api_secret', 'upstox_api_key']

    def clean_upstox_api_secret(self):
        upstox_api_secret = self.cleaned_data.get('upstox_api_secret')
        # Add any custom validation logic for upstox_api_secret if needed
        return upstox_api_secret

    def clean_upstox_api_key(self):
        upstox_api_key = self.cleaned_data.get('upstox_api_key')
        # Add any custom validation logic for upstox_api_key if needed
        return upstox_api_key
        