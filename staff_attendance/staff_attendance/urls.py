from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from .views import Login

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", Login.as_view(), name="login"),
    path("clock/", include("staff_attendance.clock.urls")),
    path("user_entry/", include("staff_attendance.user.urls")),
]
