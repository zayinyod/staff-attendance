from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from util.mixins import CustomLoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.views import View
from .forms import ClockForm
from .usecases import ClockUseCase

class ClockView(CustomLoginRequiredMixin, View):
    def get(self, request):
        form = ClockForm(user=request.user)
        return render(request, "clock/clock.html", {"form": form})

    def post(self, request):
        form = ClockForm(request.POST)

        if form.is_valid():
            try:
                ClockUseCase.create_clock_entry(request.user, form.cleaned_data)
                return redirect("clock")
            except IntegrityError:
                form.add_error(None, "Already registered.")
        return render(request, "clock/clock.html", {"form": form})

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("/")
