from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import json
import os
from datetime import datetime

from algotrading.forms import (
    CustomAuthenticationForm,
    CustomUserCreationForm,
    UpstoxForm,
)
from algotrading.models import AuthCode, StockData, AccessToken
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
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)

            response_data = {"status": "success"}
        except Exception as e:
            response_data = {"status": "error", "message": str(e)}

        return JsonResponse(response_data)

    def get(self, request):
        try:
            data = json.loads(request.body)

            file_path = BASE_DIR + "/log/debug.log"
            print(data)
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)

            response_data = {"status": "success"}
        except Exception as e:
            response_data = {"status": "error", "message": str(e)}


class UpstoxAuth(View):
    def get(self, request, user_id):
        if user_id is not None:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return HttpResponse("Invalid User", status=400)
        else:
            return HttpResponse("User required", status=400)

        code = request.GET.get("code")

        if code:
            AuthCode.objects.create(user=user, code=code)
            Upstox.api_login(user, code)
            print("Succesfull authorization")
            Discord.notify_discord(
                f"Today's Authorization done, {datetime.now().time()}"
            )
            return HttpResponse("Success", status=201)

        else:
            Discord.notify_discord("Error while getting Authorization code")
            print("NOT received")
            return HttpResponse("Error", status=500)


class UpstoxDailyLogin(View):
    def post(self, request):
        if not request.POST.get("user_id"):
            return HttpResponse("User's Login Required", status=400)

        try:
            user = User.objects.get(id=request.POST.get("user_id"))
        except User.DoesNotExist:
            return HttpResponse("Invalid User", status=400)

        return redirect(
            Upstox.BASE_API_URL
            + f"login/authorization/dialog?response_type=code&client_id={user.upstox_api_key}&redirect_uri={user.upstox_redirect_uri}"
        )


class Login(View):
    def post(self, request):
        form = CustomAuthenticationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful")
                return redirect(
                    "trade/dashboard"
                )
            else:
                messages.error(request, "Invalid login credentials")

        else:
            messages.error(request, "Invalid login credentials")
            return render(request, "algotrading/login.html", {"form": form})

    def get(self, request):
        form = CustomAuthenticationForm()
        return render(request, "algotrading/login.html", {"form": form})


def custom_logout(request):
    logout(request)
    messages.success(request, "Logout successful, Session cleared.")
    return redirect("trade/login")


class Signup(View):
    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect("trade/login")

    def get(self, request):
        form = CustomUserCreationForm()
        return render(request, "algotrading/signup.html", {"form": form})


@login_required(login_url='trade/login')
def dashboard(request):

    if not is_authenticated(request):
        messages.warning(request, 'Please log in to access your Dashboard.')
        return redirect('trade/login')

    user: User = request.user
    if (
        not user.upstox_redirect_uri
        and not user.upstox_api_key
        and not user.upstox_api_secret
    ):
        messages.add_message(
            request, messages.INFO, message="Add your Upstox credentials."
        )
    try:
        token = AccessToken.objects.latest("date")
        if token.date.date() != datetime.today().date():
            messages.add_message(
                request,
                messages.INFO,
                message="Make Today's Authorization on Upstox by clicking on 'Authorize Upstox' Button Below",
            )
        else:
            context = {
                "insights": Upstox.get_insight(
                    user,
                    datetime.combine(datetime.today(), datetime.min.time),
                    datetime.now(),
                )
            }
    except AccessToken.DoesNotExist:
        context = {}
    return render(request, "algotrading/dashboard.html", context)


class UserProfileView(View, LoginRequiredMixin):
    template_name = "algotrading/profile.html"

    def get(self, request):
        user = request.user

        if not is_authenticated(request):
            messages.warning(request, 'Please log in to access your profile.')
            return redirect('trade/login')
        
        context = {"user": user, "form": UpstoxForm(instance=user)}

        return render(request, self.template_name, context)

    def post(self, request):

        if not is_authenticated(request):
            messages.warning(request, 'Please log in to access your profile.')
            return redirect('trade/login')
        
        user = request.user
        form = UpstoxForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
        else:
            messages.error(request, form.errors)
        context = {"user": user, "form": UpstoxForm(instance=user)}
        return render(request, self.template_name, context)


def is_authenticated(request) -> bool:
    '''
        checks if the user is logged in, or not
        returns True if logged in, else False
    '''
    if not request.user.is_authenticated:
        return False
    else:
        return True