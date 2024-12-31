from django.urls import path
from .views import PaidLeaveRequestView

urlpatterns = [
    path("request/", PaidLeaveRequestView.as_view(), name="request"),
    # path("approval/", PaidLeaveApprovalView.as_view(), name="approval"),
]
