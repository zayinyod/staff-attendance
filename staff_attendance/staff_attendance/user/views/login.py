from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views import View

class Login(View):
    template_name = "user/login.html"
    redirect_url = "dashboard"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )

        if user:
            login(request, user)
            return redirect(self.redirect_url)
        else:
            return render(request, self.template_name, {"error": "Invalid user id or password."})
