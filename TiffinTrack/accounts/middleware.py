from django.shortcuts import redirect
from django.urls import resolve
from django.contrib.auth import logout
from django.contrib import messages


class RedirectAuthenticatedUserMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        # These are the names of views we want to protect
        self.protected_views = ['send_otp', 'verify_otp','login', 'register', ]

    def __call__(self, request):

        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)
        if request.user.is_authenticated:
            # Get the current view name based on the URL being accessed
            print(request.path_info)    
            print("path info")
            current_view_name = resolve(request.path_info).url_name

            print(f"{current_view_name=}")
            
            if current_view_name in self.protected_views:
                return redirect('user-home')  # Send them to the home page

        # Allow the request to continue to the next middleware/view
        response = self.get_response(request)
        return response





class BlockedUserLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("Mildware is running")
        if request.user.is_authenticated:
            if hasattr(request.user, 'is_blocked') and request.user.is_blocked:
                print(request.user.is_blocked)
                print(request.user)
                logout(request)
                messages.error(request, "Your account has been blocked.")
                return redirect('login')  # change this to your login or error page name
        return self.get_response(request)

class LoginRedirectMessageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only for unauthenticated users redirected to login
        print("Login redirect message middleware")
        if not request.user.is_authenticated:
            print("User not authenticated")
            if '/login/' in request.path and 'next' in request.GET:
                print("Setting messages")
                messages.error(request, "Please login to continue.")
        
        return self.get_response(request)