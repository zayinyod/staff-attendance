from django.urls import path
from .views import Login, Logout, UserEntry

urlpatterns = [
    path("", Login.as_view(), name="login"),
    path("logout/", Logout.as_view(), name="logout"),
    path("user_entry/", UserEntry.as_view(), name="user_entry"),
]
