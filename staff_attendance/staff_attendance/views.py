from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View

class Login(View):
    def get(self, request):
        next_url = request.GET.get("next", "/clock")
        return render(request, "login/login.html", {"next": next_url})

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.POST.get("next", "/clock")
            return redirect(next_url)
        else:
            return render(request, "login/login.html", {"error": "Invalid user id or password."})
