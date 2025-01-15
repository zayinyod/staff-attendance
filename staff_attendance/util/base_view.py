from util.mixins import CustomLoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.views import View

class BaseView(CustomLoginRequiredMixin, View):
    template_name = None
    form_class = None
    success_url = None

    def get_context_data(self, **kwargs):
        return kwargs

    def get(self, request):
        form = self.form_class(user=request.user)
        return render(request, self.template_name, self.get_context_data(form=form))

    def post(self, request):
        form = self.form_class(request.POST, user=request.user)

        if form.is_valid():
            try:
                self.form_valid(form)
                return redirect(self.success_url)
            except IntegrityError as e:
                print(f"IntegrityError: {e}")
                form.add_error(None, "This record already exists.")

        return render(request, self.template_name, self.get_context_data(form=form))

    def form_valid(self, form):
        raise NotImplementedError("Subclasses must implement `form_valid` method.")
