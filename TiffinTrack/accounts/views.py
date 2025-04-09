from django.shortcuts import render, redirect
from .utils import login_redirect_view
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


#TODO dont give access to admin

def accounts_login(request):

    if request.user.is_authenticated and  not request.user.is_admin:
        messages.success(request,"Logged in as admin")
        return login_redirect_view(request)
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(login_redirect_view(request))
        else:
            print("Invalid credentials")
            messages.success(request, "Invalid username or password")
    return render(request, './accounts/login.html')

def accounts_sign_up(request):
    return render(request, './accounts/sign-up.html')