from django.shortcuts import render,redirect
from django.views import View
from django.http import JsonResponse,HttpResponse
from django.conf import settings
import json
import os
from datetime import datetime

from algotrading.models import AuthCode, StockData
from algotrading.controller import Upstox
from notification.controller import Discord
from user.models import User

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ChartinkWebhook(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)

            file_path = BASE_DIR + "/log/debug.log"
            print(data)
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)


            response_data = {'status': 'success'}
        except Exception as e:
            response_data = {'status': 'error', 'message': str(e)}

        return JsonResponse(response_data)
    
    def get(self, request):
        try:
            data = json.loads(request.body)

            file_path = BASE_DIR + "/log/debug.log"
            print(data)
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)


            response_data = {'status': 'success'}
        except Exception as e:
            response_data = {'status': 'error', 'message': str(e)}
    
class UpstoxAuth(View):
    def get(self, request, user_id):
        if user_id is not None:
            try:
                user = User.objects.get(id = user_id)
            except User.DoesNotExist:
                return HttpResponse('Invalid User', status = 400)
        else:
           return HttpResponse('User required', status = 400) 

        code = request.GET.get('code')

        if code:
            AuthCode.objects.create(
                user = user,
                code = code
            )
            Upstox.api_login(user, code)
            print("Succesfull authorization")
            Discord.notify_discord(f"Today's Authorization done, {datetime.now().time()}")
            return HttpResponse("Success", status=201)
            
        else:
            Discord.notify_discord("Error while getting Authorization code")
            print("NOT received")
            return HttpResponse("Error",status=500)
        
class UpstoxDailyLogin(View):
    def post(self, request):
        if not request.POST.get('user_id'):
            return HttpResponse("User's Login Required",status = 400)
        
        try:
            user = User.objects.get(id = request.POST.get('user_id'))
        except User.DoesNotExist:
            return HttpResponse("Invalid User",status = 400)

        return redirect(Upstox.BASE_API_URL + f'login/authorization/dialog?response_type=code&client_id={user.upstox_api_key}&redirect_uri={user.upstox_redirect_uri}')


def test_func(request):
    obj = Upstox()
    obj.morning_update()
    return HttpResponse("success",status=200)