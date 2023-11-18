from django.db import models
from django.utils import timezone
from user.models import User

# Create your models here.


class AuthCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=25)
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True)


class AccessToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user","token","-date"])
            ]



class UserFund(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    available_money = models.FloatField(max_length=25)
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.email}'s balance -> {self.available_money}"


class NseSheetStock(models.Model):
    symbl = models.CharField(primary_key=True, max_length=25, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["symbl"])
            ]
        


class StockData(models.Model):
    symbl = models.CharField(primary_key=True, max_length=15)
    rate = models.FloatField(max_length=20, null=True, blank=True)
    instrument_symbl = models.CharField(max_length=40)
    day_open = models.FloatField(max_length=40, default=0)
    day_high = models.FloatField(max_length=40, default=40)

    class Meta:
        indexes = [models.Index(fields=["symbl"])]

class StockTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    symbl = models.ForeignKey(StockData, on_delete=models.PROTECT)
    price = models.FloatField(max_length=40, default=0)
    rate = models.FloatField(max_length=20, default=0)
    quantity = models.IntegerField(default= 0)
    datetime = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=10,help_text='SELL OR BOUGHT')
    closed = models.BooleanField(default=False)

