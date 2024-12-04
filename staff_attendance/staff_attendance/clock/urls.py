from django.urls import path
from .views import ClockView, Logout

urlpatterns = [
    path("", ClockView.as_view(), name="clock"),
    path("logout/", Logout.as_view(), name="logout"),
]
