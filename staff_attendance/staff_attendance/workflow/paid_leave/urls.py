from django.urls import path
from .views import PaidLeaveRequestView

urlpatterns = [
    path("", PaidLeaveRequestView.as_view(), name="paid_leave_request"),
]
