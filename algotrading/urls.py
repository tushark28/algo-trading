from django.urls import path
from algotrading.views import *

urlpatterns =[
    path('upstox-auth/<int:user_id>', UpstoxAuth.as_view()),
    path('daily-auth',UpstoxDailyLogin.as_view()),
    path('test',test_func),
    path('chartink',ChartinkWebhook.as_view()),

]