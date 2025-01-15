from util.base_view import BaseView
from .forms import PaidLeaveRequestForm
from .usecases import PaidLeaveEntry

class PaidLeaveRequestView(BaseView):
    template_name = "workflow/paid_leave/request.html"
    form_class = PaidLeaveRequestForm
    success_url = "paid_leave_request"

    def form_valid(self, form):
        PaidLeaveEntry.create_request(self.request.user, form.cleaned_data)
