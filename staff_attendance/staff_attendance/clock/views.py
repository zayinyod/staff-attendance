from django.shortcuts import render, redirect
from django.views import View
from .forms import ClockForm
from .usecases import ClockUsecase

class Clock(View):
    def get(self, request):
        form = ClockForm()
        return render(request, "clock/clock.html", {"form": form})

    def post(self, request):
        form = ClockForm(request.POST)

        if form.is_valid():
            ClockUsecase().create_clock_entry(form.cleaned_data)
            return redirect("login")
        return render(request, "clock/clock.html", {"form": form})
