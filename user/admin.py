from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from user.models import User
# Register your models here.
class FundAdmin(UserAdmin):
    list_display = ['id','username','email']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Upstox Info', {'fields': ('upstox_redirect_uri', 'upstox_api_secret', 'upstox_api_key')}),
    )

admin.site.register(User, FundAdmin)