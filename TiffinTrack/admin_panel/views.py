from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from users.forms import UserRegisterForm
from users.models import CustomUser
from django.views.decorators.cache import never_cache


def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin-home')
    if request.method == "POST":
        username = request.POST.get("username")  # Avoids KeyError
        password = request.POST.get("password")  # Fetch password safely
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin-home')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, './admin_panel/login.html')


def admin_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('admin-login')

# @never_cache
# @login_required(login_url='admin-login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')
    username = request.POST.get("username")
    if request.method == 'POST' and username:
        print(f"{username=}")
        users = CustomUser.objects.filter(username=username)
    else:
        users = CustomUser.objects.all()
    context = {
        'users': users
    }
    return render(request, './admin_panel/users.html', context)


@never_cache
@login_required(login_url='admin-login')
def delete(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('admin-home')

@never_cache
@login_required(login_url='admin-login')
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-home')            
    else:
        form = UserRegisterForm()
    context = {  
        'form':form  
    }  
    return render(request, './admin_panel/register.html', context)  
    

@never_cache
@login_required(login_url='admin-login')
def update(request, id):
    user = get_object_or_404(CustomUser, id=id)
    # if request.method == 'POST':
    #     form = UserUpdateForm(request.POST, instance=user)  # Pre-fill with existing user data
    #     if form.is_valid():
    #         form.save()
    #         return redirect('admin-home')  # Redirect to the profile page
    # else:
    #     form = UserUpdateForm(instance=user)  # Pre-fill with existing user data

    return render(request, './admin_panel/update.html', {'form': form})




    


def restaurants(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')

    restaurants = CustomUser.objects.all()
    context = {
        'users': restaurants
    }
    return render(request, './admin_panel/restaurants.html', context)
