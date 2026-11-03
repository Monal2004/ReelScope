from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


@require_GET
def register(request):
    """Public registration is disabled.

    Staff accounts are created through Django's superuser/admin system.
    Redirect visitors to the login page with an informative message.
    """
    messages.info(
        request,
        "Public registration is disabled. Staff accounts are created "
        "by the administrator through Django Admin.",
    )
    return redirect("accounts:login")
