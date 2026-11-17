from util.base_superuser_view import BaseSuperUserView
from util.base_user_view import BaseUserView
from django.db import transaction
from django.shortcuts import redirect
from .paid_leave.usecases import PaidLeaveEntry

class WorkflowSelectView(BaseSuperUserView):
    template = "workflow/select_menu.html"

class RequestView(BaseUserView):
    template = "workflow/request_menu.html"

class ApprovalView(BaseSuperUserView):
    template = "workflow/approval.html"

    status_prefix = "status_"
    approvable_codes = ("1", "2")

    def get_context_data(self, request):
        return {"pending_list": PaidLeaveEntry.pending()}

    def post(self, request):
        with transaction.atomic():
            for key, value in request.POST.items():
                request_id = self.extract_request_id(key)
                if request_id is None or value not in self.approvable_codes:
                    continue

                PaidLeaveEntry.approve(request_id, value, request.user)

        return redirect("approval")

    @classmethod
    def extract_request_id(cls, key: str) -> str:
        """
        POSTキーから申請IDを取り出す。
        対象外のキーおよび数値でないIDはNoneを返す。
        """
        if not key.startswith(cls.status_prefix):
            return None

        request_id = key.removeprefix(cls.status_prefix)

        return request_id if request_id.isdecimal() else None
