from django.shortcuts import redirect
from django.urls import resolve, Resolver404
from django.contrib.auth import logout
from django.contrib import messages
from restaurant.models import Subscriptions
from .utils import login_redirect_view


class RedirectAuthenticatedUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_views = [
            "send_otp",
            "verify_otp",
            "login",
            "register",
        ]

    def __call__(self, request):

        if request.path.startswith("/admin/") or request.path.startswith("/static/"):
            return self.get_response(request)

        if request.user.is_authenticated:
            try:
                current_view = resolve(request.path_info)
                current_view_name = current_view.url_name
            except Resolver404:
                return self.get_response(request)

            if current_view_name in self.protected_views:
                return redirect(login_redirect_view(request))

            # Prevent admin/staff/restaurant users from accessing normal-user routes.
            if (
                current_view.func.__module__.startswith("users.views")
                and not request.user.is_normal_user
            ):
                return redirect(login_redirect_view(request))
        response = self.get_response(request)
        return response


class BlockedUserLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, "is_blocked") and request.user.is_blocked:
                logout(request)
                messages.error(request, "Your account has been blocked.")
                return redirect("login")  # change this to your login or error page name
        return self.get_response(request)


class LoginRedirectMessageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if "/login/" in request.path and "next" in request.GET:
                messages.error(request, "Please login to continue.")
        return self.get_response(request)


class CheckSubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_normal_user:
            subscriptions = Subscriptions.objects.filter(
                user=request.user, is_active=True
            )

            for subscription in subscriptions:
                if not subscription.orders.filter(status="PENDING").exists():
                    subscription.is_active = False
                    subscription.save()

        return self.get_response(request)
