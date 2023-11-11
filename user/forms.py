from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

added_fields = ('upstox_redirect_uri','upstox_api_key','upstox_api_secret')

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + added_fields

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = UserChangeForm.Meta.fields + added_fields