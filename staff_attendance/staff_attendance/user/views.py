from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import UserEntryForm

class UserEntry(CreateView):
    form_class = UserEntryForm
    template_name = "user/user_entry.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


