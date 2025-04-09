from django.shortcuts import redirect
from django.urls import resolve

class RedirectAuthenticatedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # These are the names of views we want to protect
        self.protected_views = ['send_otp', 'verify_otp','login', 'register', ]

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get the current view name based on the URL being accessed
            current_view_name = resolve(request.path_info).url_name
            
            if current_view_name in self.protected_views:
                return redirect('user-home')  # Send them to the home page

        # Allow the request to continue to the next middleware/view
        response = self.get_response(request)
        return response
