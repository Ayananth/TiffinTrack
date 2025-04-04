from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from users.forms import UserRegisterForm
from users.models import CustomUser
from django.views.decorators.cache import never_cache
from restaurant.models import RestaurantProfile


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


@never_cache
@login_required(login_url='admin-login')
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
def restaurants(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')

    restaurants = RestaurantProfile.objects.all()
    context = {
        'restaurants': restaurants
    }
    return render(request, './admin_panel/restaurants.html', context)


@never_cache
@login_required(login_url='admin-login')
def restaurant_requests(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')

    restaurants = RestaurantProfile.objects.filter(is_approved=False)
    context = {
        'restaurants': restaurants
    }
    return render(request, './admin_panel/register_restaurant.html', context)


@never_cache
@login_required(login_url='admin-login')
def restaurant_approve(request, pk):
    if not request.user.is_authenticated:
        return redirect('admin-login')
    restaurants = RestaurantProfile.objects.get(pk=pk)
    if request.method == "POST":
        restaurants.is_approved = True
        restaurants.save()
        return redirect('restaurant_request')
    context = {
        'restaurants': restaurants
    }
    return render(request, './admin_panel/restaurant_approve.html', context)


@never_cache
@login_required(login_url='admin-login')
def delete_restaurant(request, id):
    restaurant = get_object_or_404(RestaurantProfile, pk=id)
    restaurant.delete()
    return redirect('restaurant_request')