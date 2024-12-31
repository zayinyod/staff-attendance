from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View

class Logout(View):
    redirect_url = "/"

    def get(self, request):
        logout(request)
        return redirect(self.redirect_url)
