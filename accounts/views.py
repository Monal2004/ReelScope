from django.contrib.auth import views as auth_views
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .forms import RegisterForm


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


@require_GET
def register(request):
    """Registration page. The account-creation flow arrives in the backend phase."""
    return render(request, "accounts/register.html", {"form": RegisterForm()})
