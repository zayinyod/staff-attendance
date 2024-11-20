from django.db import IntegrityError
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from .forms import UserEntryForm
from .usecases import UserUseCase

class UserEntry(CreateView):
    form_class = UserEntryForm
    template_name = "user/user_entry.html"

    def form_valid(self, form):
        try:
            UserUseCase.create_user_entry(form.cleaned_data)
            return redirect("login")
        except IntegrityError:
            form.add_error(None, "Username already exists.")
            return self.form_invalid(form)
