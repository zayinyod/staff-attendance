from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class CustomLoginRequiredMixin(LoginRequiredMixin):
    """
    未承認ユーザーをログインページにリダイレクトするためのミックスイン
    """

    def handle_no_permission(self: object) -> object:
        if self.raise_exception or self.request.user.is_authenticated:
            return super().handle_no_permission()
        else:
            return redirect(self.get_login_url())
