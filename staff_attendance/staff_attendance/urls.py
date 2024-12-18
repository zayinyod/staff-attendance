from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("staff_attendance.user.urls")),
    path("clock/", include("staff_attendance.clock.urls")),
    path("workflow/", include("staff_attendance.workflow.urls")),
]
