from django.urls import path
from .views import ClockView, DashboardView

urlpatterns = [
    path("", ClockView.as_view(), name="clock"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
