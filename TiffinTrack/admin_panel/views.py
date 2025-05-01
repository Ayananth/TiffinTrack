from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import AdminUserRegisterForm, UserUpdateForm, RestaurantRegisterForm, FoodItemManageForm
from accounts.models import CustomUser
from django.views.decorators.cache import never_cache
from restaurant.models import RestaurantProfile, FoodItem
from django.core.paginator import Paginator




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
    return render(request, './admin_panel/dashboard.html', context)

@login_required(login_url='admin-login')
def all_users(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')
    username = request.POST.get("username")
    if request.method == 'POST' and username:
        print(f"{username=}")
        users = CustomUser.objects.filter(username=username).order_by('-created_at')
    else:
        users = CustomUser.objects.all().order_by('-created_at')
    # Pagination logic
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        # 'users': users,
        'page_obj': page_obj
    }
    return render(request, './admin_panel/all_users.html', context)


@login_required(login_url='admin-login')
def add_users(request):
    if request.method == "POST":
        print(request.POST.dict())  # cleaner view
        print("Adding new user by admin")
        form = AdminUserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"User created for {username}")
            return redirect('all-users')
        else:
            print("Form not valid")
            messages.error(request, "Form not valid")
            return render(request, './admin_panel/add_user.html', {'form': form})

    print("Add new user menu from admin side")
    form = AdminUserRegisterForm()
    context = {
        'form': form
    }

    return render(request, './admin_panel/add_user.html', context)


@never_cache
@login_required(login_url='admin-login')
def restaurants(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')
    

    restaurants = RestaurantProfile.objects.all().order_by('is_approved','-created_at')
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


@login_required()
def restaurant_add_or_update(request, pk=None):
    if pk:
        restaurant_obj = get_object_or_404(RestaurantProfile, pk=pk)
    else:
        restaurant_obj = None

    if request.method == "POST":
        form = RestaurantRegisterForm(request.POST, request.FILES, instance=restaurant_obj)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.user_type = 'restaurant'
            restaurant.save()
            name = form.cleaned_data.get('restaurant_name')
            messages.success(request, f"Restaurant {name} {'Updated' if pk else 'Created'}!")
            return redirect('restaurants')
        else:
            messages.error(request, "Invalid inputs.")
    else:
        form = RestaurantRegisterForm(instance=restaurant_obj)
        food_items = FoodItem.objects.select_related('menu_category').filter(restaurant=restaurant_obj)
        print(food_items)

    return render(request, './admin_panel/add-restaurant.html', {'form': form,
                                                                 'food_items': food_items})

    

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
    return redirect('restaurants')

@never_cache
@login_required(login_url='admin-login')
def delete_user(request, id):
    user = get_object_or_404(CustomUser, pk=id)
    user.delete()
    messages.success(request,"User deleted")
    return redirect('all-users')




@never_cache
@login_required(login_url='admin-login')
def update_user(request, id):
    print("_-------------------------------")
    user = get_object_or_404(CustomUser, id=id)
    print(user.is_blocked)
    print("_-------------------------------")
    if request.method == 'POST':
        print("Updating user by admin")
        print(request.POST.dict())
        print("Updating user by admin")
        form = UserUpdateForm(request.POST, instance=user)  # Pre-fill with existing user data
        if form.is_valid():
            print("Form is valid")
            form.save()
            messages.success(request, "User updated successfully")
            return redirect('update-user', id=id)  # Redirect to the profile page
        else:
            messages.error(request, "Form not valid")
            print("Form not valid")
            print(form.errors)
            return redirect('update-user', id=id)   
        
    else:
        print("Else")
        form = UserUpdateForm(instance=user)  # Pre-fill with existing user data

    return render(request, './admin_panel/update_user.html', {'form': form})



