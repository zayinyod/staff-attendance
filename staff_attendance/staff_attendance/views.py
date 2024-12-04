from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views import View

class Login(View):
    def get(self, request):
        return render(request, "login/login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/clock")
        else:
            return render(request, "login/login.html", {"error": "Invalid user id or password."})
