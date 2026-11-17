from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("features.user.urls")),
    path("clock/", include("features.clock.urls")),
    path("workflow/", include("features.workflow.urls")),
]
