from util.mixins import CustomLoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View

class BaseSuperUserView(CustomLoginRequiredMixin, View):
    template = None
    forbidden_template = "403.html"

    def get_context_data(self, request):
        return {}

    def get(self, request):
        if not request.user.is_superuser:
            return render(request, self.forbidden_template, status=403)
        context = self.get_context_data(request)

        return render(request, self.template, context)
