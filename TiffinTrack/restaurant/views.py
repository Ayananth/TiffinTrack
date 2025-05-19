from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from accounts.forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from .models import RestaurantProfile, MenuCategory, FoodCategory, FoodItem
from .forms import RestaurantProfileForm, MenuCategoryForm
from users.models import Orders



from django.db.models import Count
from django.utils.timezone import now
from django.db.models import Count, Q
from django.utils.timezone import localtime
from datetime import datetime
from accounts.models import CustomUser, UserProfile
from .models import Subscriptions



# def restaurant_login(request):
    
#     if request.user.is_authenticated:
#         return redirect('restaurant-home')
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             print("logging in")
#             login(request, user)
#             return redirect('restaurant-home')
#         else:
#             print("Invalid credentials")
#             messages.success(request, "Invalid username or password")
#     return render(request, './restaurant/login.html')


# @login_required(login_url='login')
def home(request):
    print("Home page")
    print(request.user)
    # if not request.user.is_restaurant_user:
    #     print("not restaurant user")
    #     messages.error(request, "not restaurant user")

        # return render(request, './restaurant/login.html')
    today = '2025-05-19'
    # selected_date = localtime().date()
    # today = selected_date
    selected_date = today
    print(today)
    restaurant = get_object_or_404(RestaurantProfile, user=request.user)

    date_str = request.GET.get('date')
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else now().date()
    except ValueError:
        selected_date = now().date()


    # Total orders per food category for today
    food_category_orders = (
        Orders.objects.filter(
            delivery_date=selected_date,
            restaurant=restaurant
        )
        .values('food_category__name')
        .annotate(total_orders=Count('id'))
        .order_by('food_category__name')
    )
    print(f"{food_category_orders=}")
    # Cancelled orders per food category for today
    cancelled_orders = (
        Orders.objects.filter(
            delivery_date=selected_date,
            restaurant=restaurant,
            status='CANCELLED'
        )
        .values('food_category__name')
        .annotate(cancelled_orders=Count('id'))
        .order_by('food_category__name')
    )
    print(f"{cancelled_orders=}")

    # Merge both querysets into a single list of dicts
    data = {}
    for item in food_category_orders:
        name = item['food_category__name'] or 'Unknown'
        data[name] = {'category': name, 'total_orders': item['total_orders'], 'cancelled_orders': 0}
    for item in cancelled_orders:
        name = item['food_category__name'] or 'Unknown'
        if name in data:
            data[name]['cancelled_orders'] = item['cancelled_orders']
        else:
            data[name] = {'category': name, 'total_orders': 0, 'cancelled_orders': item['cancelled_orders']}

    context = {
        'dashboard_data': data.values(),
        'restaurant': restaurant,
        'selected_date': selected_date
    }
    return render(request, './restaurant/dashboard.html', context)


def restaurant_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('login')


# @login_required(login_url='login')
def restaurant_register(request):
    # if request.user.is_authenticated:
    #     return redirect('restaurant-home')
    return render(request, './restaurant/home.html')  




#Menu Category Views

@login_required(login_url='login')
def menu_category_list(request):
    # Assuming the user is logged in and has a restaurant profile
    restaurant = request.user.restaurantprofile
    menu_categories = MenuCategory.objects.filter(restaurant=restaurant)
    print(f"{menu_categories.values()=}")
    context = {
        'menu_categories': menu_categories,
    }
    return render(request, 'restaurant/menu.html', context)


@login_required(login_url='login')
def menu_category_add(request):
    restaurant = RestaurantProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST)
        if form.is_valid():
            if MenuCategory.objects.filter(restaurant=restaurant, name=form.cleaned_data.get('name')).exists():
                messages.error(request, f"A category with the name already exists for this restaurant.")
                return redirect('menu_category_add')                
            menu_category = form.save(commit=False)
            menu_category.restaurant = restaurant
            menu_category.save()
            return redirect('menu_category_list')
    else:
        form = MenuCategoryForm()

    return render(request, 'restaurant/add_menu_category.html', {'form': form})


@login_required(login_url='login')
def menu_category_edit(request, pk):
    menu_category = get_object_or_404(MenuCategory, pk=pk)
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST, instance=menu_category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu category updated successfully!')
            return redirect('menu_category_list')
    else:
        form = MenuCategoryForm(instance=menu_category)
    
    return render(request, 'restaurant/add_menu_category.html', {'form': form, 'action': 'Edit'})


@login_required(login_url='login')
def menu_category_delete(request, pk):
    menu_category = get_object_or_404(MenuCategory, pk=pk)
    print(f"{menu_category=}")
    if menu_category:
        print("Deleting menu category")
        menu_category.delete()
        messages.success(request, 'Menu category deleted successfully!')
        return redirect('menu_category_list')
    print("Not deleting menu category")
    
    return render(request, 'restaurant/menu.html')








# Food Category Views

@login_required(login_url='login')
def food_category_list(request):
    print(f"{request.user.restaurantprofile=}")
    restaurant = request.user.restaurantprofile
    food_categories = FoodCategory.objects.filter(restaurant=restaurant)
    return render(request, 'restaurant/food_category_list.html', {'food_categories': food_categories})



def users(request):


    restaurant = get_object_or_404(RestaurantProfile, user=request.user)
    subscriptions = Subscriptions.objects.filter(restaurant=restaurant, user__isnull=False)

    for sub in subscriptions:
        if sub.user is not None:
            print(sub.user.email)



    # Pagination logic
    paginator = Paginator(subscriptions, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj
    }
    return render(request, './restaurant/all_users.html', context)