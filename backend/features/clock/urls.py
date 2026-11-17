from django.urls import path
from .views import ClockView, DashboardView, TimesheetsView

urlpatterns = [
    path("", ClockView.as_view(), name="clock"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("timesheets/", TimesheetsView.as_view(), name="timesheets"),
]
