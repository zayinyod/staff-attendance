from django.urls import path, include
from .views import SuperUserSelectView, RequestView, ApprovalView

urlpatterns = [
    path("", SuperUserSelectView.as_view(), name="select"),
    path("request/", RequestView.as_view(), name="request"),
    path("request/paid_leave/", include("staff_attendance.workflow.paid_leave.urls")),
    path("approval/", ApprovalView.as_view(), name="approval"),
]
