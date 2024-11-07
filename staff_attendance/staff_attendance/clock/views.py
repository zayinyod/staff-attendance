from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from .forms import ClockForm
from .usecases import ClockUseCase

class Clock(LoginRequiredMixin, View):
    def get(self, request):
        form = ClockForm(user=request.user)
        return render(request, "clock/clock.html", {"form": form})

    def post(self, request):
        form = ClockForm(request.POST)

        if form.is_valid():
            ClockUseCase(user=request.user).create_clock_entry(form.cleaned_data)
            return redirect("login")
        return render(request, "clock/clock.html", {"form": form})

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("/")
