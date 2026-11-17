from util.mixins import CustomLoginRequiredMixin
from django.shortcuts import render
from django.views import View


class BaseUserView(CustomLoginRequiredMixin, View):
    """
    ユーザ向けのViewの基底クラス
    """

    template = None

    def get_context_data(self, request) -> dict:
        return {}

    def get(self, request):
        context = self.get_context_data(request)
        return render(request, self.template, context)
