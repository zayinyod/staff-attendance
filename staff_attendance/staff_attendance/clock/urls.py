from django.urls import path
from .views import Clock, Logout

urlpatterns = [
    path("", Clock.as_view(), name="clock"),
    path("logout/", Logout.as_view(), name="logout"),
]
