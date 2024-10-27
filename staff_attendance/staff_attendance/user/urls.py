from django.urls import path
from .views import UserEntry

urlpatterns = [
    path("", UserEntry.as_view(), name="user_entry"),
]
