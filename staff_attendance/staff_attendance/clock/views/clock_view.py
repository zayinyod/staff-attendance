from util.base_form_view import BaseFormView
from ..forms import ClockForm
from ..usecases import ClockEntry

class ClockView(BaseFormView):
    template_name = "clock/clock.html"
    form_class = ClockForm
    success_url = "clock"

    def form_valid(self, form):
        ClockEntry.create_clock_entry(self.request.user, form.cleaned_data)
