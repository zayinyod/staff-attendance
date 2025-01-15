from util.mixins import CustomLoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from .paid_leave.usecases import PaidLeaveEntry

class SuperUserSelectView(CustomLoginRequiredMixin, View):
    template = "workflow/select_menu.html"
    forbidden_template = "403.html"

    def get(self, request):
        if not request.user.is_superuser:
            return render(request, self.forbidden_template, status=403)
        return render(request, self.template)

class RequestView(CustomLoginRequiredMixin, View):
    template = "workflow/request_menu.html"

    def get(self, request):
        return render(request, self.template)

class ApprovalView(CustomLoginRequiredMixin, View):
    template = "workflow/approval.html"
    forbidden_template = "403.html"

    def get(self, request):
        if not request.user.is_superuser:
            return render(request, self.forbidden_template, status=403)
        pending_list = PaidLeaveEntry.pending()

        return render(request, self.template, {"pending_list": pending_list})

    def post(self, request):
        if not request.user.is_superuser:
            return render(request, self.forbidden_template, status=403)

        for key, value in request.POST.items():
            if key.startswith("status_"):
                _, id = key.split("_")
                if value in ["1", "2"]:
                    PaidLeaveEntry.approve(id, value, request.user)

        return redirect("approval")
