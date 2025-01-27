from util.mixins import CustomLoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View

class BaseUserView(CustomLoginRequiredMixin, View):
    template = None

    def get_context_data(self, request):
        return {}

    def get(self, request):
        context = self.get_context_data(request)
        return render(request, self.template, context)
