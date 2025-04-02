from util.base_form_view import BaseFormView
from .forms import PaidLeaveRequestForm
from .usecases import PaidLeaveEntry

class PaidLeaveRequestView(BaseFormView):
    template_name = "workflow/paid_leave/request.html"
    form_class = PaidLeaveRequestForm
    success_url = "paid_leave_request"

    def form_valid(self, form):
        PaidLeaveEntry.create_request(self.request.user, form.cleaned_data)
