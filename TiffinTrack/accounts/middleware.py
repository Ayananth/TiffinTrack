from django.shortcuts import redirect
from django.urls import resolve
from django.contrib.auth import logout
from django.contrib import messages


class RedirectAuthenticatedUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_views = ['send_otp', 'verify_otp','login', 'register', ]

    def __call__(self, request):

        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)
        if request.user.is_authenticated:
            current_view_name = resolve(request.path_info).url_name            
            if current_view_name in self.protected_views:
                return redirect('user-home')
        response = self.get_response(request)
        return response


class BlockedUserLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'is_blocked') and request.user.is_blocked:
                logout(request)
                messages.error(request, "Your account has been blocked.")
                return redirect('login')  # change this to your login or error page name
        return self.get_response(request)

class LoginRedirectMessageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if '/login/' in request.path and 'next' in request.GET:
                messages.error(request, "Please login to continue.")
        return self.get_response(request)