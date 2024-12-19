from util.base_view import BaseView
from .forms import PaidLeaveRequestForm
from .usecases import PaidLeaveEntry

class PaidLeaveRequestView(BaseView):
    template_name = "workflow/request.html"
    form_class = PaidLeaveRequestForm
    success_url = "request"

    def form_valid(self, form):
        PaidLeaveEntry.create_paid_leave_request(self.request.user, form.cleaned_data)
