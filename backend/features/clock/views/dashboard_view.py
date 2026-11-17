from util.mixins import CustomLoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views import View
from ..usecases import ClockCalculate

class DashboardView(CustomLoginRequiredMixin, View):
    template_name = "clock/dashboard.html"

    def get(self, request):
        date, has_invalid_date = self.resolve_date(request.GET.get("date"))
        summary = ClockCalculate.daily_summary(request.user, date)
        context = {
            "summary": summary,
            "date": date,
            "has_invalid_date": has_invalid_date,
        }
        return render(request, self.template_name, context)

    @staticmethod
    def resolve_date(value: str) -> tuple:
        """
        クエリパラメータの日付をdate型に変換する。
        未指定もしくは不正な値の場合は当日を返す。
        """
        if not value:
            return timezone.localdate(), False

        try:
            parsed_date = parse_date(value)
        except ValueError:
            parsed_date = None

        if parsed_date is None:
            return timezone.localdate(), True

        return parsed_date, False
