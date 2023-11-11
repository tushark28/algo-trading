from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin
# Create your models here.

class User(AbstractUser):
    upstox_redirect_uri = models.URLField(blank=True, null=True)
    upstox_api_secret = models.TextField(blank=True,null=True, max_length=50)
    upstox_api_key = models.TextField(blank=True,null=True,max_length=70)
