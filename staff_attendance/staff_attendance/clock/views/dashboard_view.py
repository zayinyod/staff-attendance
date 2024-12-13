from util.mixins import CustomLoginRequiredMixin
from datetime import datetime
from django.shortcuts import render
from django.views import View
from ..usecases import ClockCalculate

class DashboardView(CustomLoginRequiredMixin, View):
    template_name = "clock/dashboard.html"

    def get(self, request):
        user = request.user
        date = request.GET.get("date")

        if not date:
            date = datetime.today().date()

        summary = ClockCalculate.daily_summary(user, date)
        context = {
            "summary": summary,
            "date": date,
        }
        return render(request, self.template_name, context)
