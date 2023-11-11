from django.contrib import admin
from algotrading.models import *

# Register your models here.
# class CodeAdmin(admin.ModelAdmin):
#     list_display = ['id','code','date']
#     list_filter = ['date']

# admin.site.register(Code, CodeAdmin)

class TokenAdmin(admin.ModelAdmin):
    list_display = ['user','token','date']
    list_filter = ['date']

admin.site.register(AccessToken, TokenAdmin)

class FundAdmin(admin.ModelAdmin):
    list_display = ['user','available_money','date']
    list_filter = ['date']

admin.site.register(UserFund, FundAdmin)

# class nseAdmin(admin.ModelAdmin):
#     list_display = ['symbl']

# admin.site.register(NseSheetStocks, nseAdmin)

class stockdataAdmin(admin.ModelAdmin):
    list_display = ['symbl','price','day_open','day_high','price_bought','instrument_symbl']

admin.site.register(StockData, stockdataAdmin)

