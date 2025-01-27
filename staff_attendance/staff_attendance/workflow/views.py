from util.base_superuser_view import BaseSuperUserView
from util.base_user_view import BaseUserView
from django.shortcuts import render, redirect
from .paid_leave.usecases import PaidLeaveEntry

class WorkflowSelectView(BaseSuperUserView):
    template = "workflow/select_menu.html"

class RequestView(BaseUserView):
    template = "workflow/request_menu.html"

class ApprovalView(BaseSuperUserView):
    template = "workflow/approval.html"

    def get_context_data(self, request):
        return {"pending_list": PaidLeaveEntry.pending()}

    def post(self, request):
        if not request.user.is_superuser:
            return render(request, self.forbidden_template, status=403)

        for key, value in request.POST.items():
            if key.startswith("status_"):
                _, id = key.split("_")
                if value in ["1", "2"]:
                    PaidLeaveEntry.approve(id, value, request.user)

        return redirect("approval")
