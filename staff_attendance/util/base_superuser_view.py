from util.mixins import CustomLoginRequiredMixin
from django.shortcuts import render
from django.views import View


class BaseSuperUserView(CustomLoginRequiredMixin, View):
    """
    スーパーユーザ向けのViewの基底クラス
    """

    template = None
    forbidden_template = "403.html"

    def dispatch(self, request, *args, **kwargs):
        """
        HTTPメソッドを問わず権限を検証する。
        未認証の場合はCustomLoginRequiredMixinがログインページへ誘導する。
        """
        if request.user.is_authenticated and not request.user.is_superuser:
            return render(request, self.forbidden_template, status=403)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, request) -> dict:
        return {}

    def get(self, request):
        return render(request, self.template, self.get_context_data(request))
