from django.urls import path
from algotrading.views import *

urlpatterns =[
    path('upstox-auth/<int:user_id>', UpstoxAuth.as_view()),
    path('daily-auth',UpstoxDailyLogin.as_view()),
    path('chartink',ChartinkWebhook.as_view()),
    path('login/', Login.as_view(), name='trade/login'),
    path('logout/', custom_logout, name='trade/logout'),
    path('signup/', Signup.as_view(), name='trade/signup'),
    path('dashboard/', dashboard, name='trade/dashboard'),
    path('profile/',UserProfileView.as_view(),name='trade/profile')
]