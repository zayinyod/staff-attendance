from util.mixins import CustomLoginRequiredMixin
from datetime import date, timedelta
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from ..forms import MonthSelectForm
from ..usecases import ClockCalculate

class TimesheetsView(CustomLoginRequiredMixin, View):
    """
    月単位の勤怠一覧を表示する
    """

    template_name = "clock/timesheets.html"

    def get(self, request):
        year, month, has_invalid_month = self.resolve_month(request.GET)
        detail = ClockCalculate.monthly_detail(request.user, year, month)
        first_day = date(year, month, 1)

        context = {
            "form": MonthSelectForm(initial={"year": year, "month": month}),
            "daily_records": detail["daily_records"],
            "totals": detail["totals"],
            "current_month": first_day,
            "previous_month": self.previous_month(first_day),
            "next_month": self.next_month(first_day),
            "has_invalid_month": has_invalid_month,
        }
        return render(request, self.template_name, context)

    @classmethod
    def resolve_month(cls, query_params) -> tuple:
        """
        クエリパラメータの年月を検証する。
        未指定もしくは不正な値の場合は当月を返す。
        """
        today = timezone.localdate()

        if not query_params:
            return today.year, today.month, False

        form = MonthSelectForm(query_params)
        if not form.is_valid():
            return today.year, today.month, True

        return int(form.cleaned_data["year"]), int(form.cleaned_data["month"]), False

    @classmethod
    def previous_month(cls, first_day: date):
        """
        選択可能な範囲を超える場合はNoneを返す
        """
        previous = first_day - timedelta(days=1)

        return previous if previous.year in MonthSelectForm.selectable_years() else None

    @classmethod
    def next_month(cls, first_day: date):
        following = (first_day + timedelta(days=31)).replace(day=1)

        return following if following.year in MonthSelectForm.selectable_years() else None
