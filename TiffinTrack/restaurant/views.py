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
from .forms import FoodItemManageForm, MenuManageForm, FoodCategoryManageForm



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


@login_required(login_url='login')
def home(request):
    print("Home page")
    print(request.user)
    if request.user.user_type != 'restaurant':
        messages.error(request, "Not restaurant user")
        return redirect('login')
    
    today = '2025-05-19'
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

@login_required(login_url='login')
def restaurant_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('login')


@login_required(login_url='login')
def restaurant_register(request):

    if RestaurantProfile.objects.filter(user=request.user, is_approved=True).exists():
        messages.success(request, "Manage your restaurant")
        return redirect('restaurant-home')

    try:
        restaurant = RestaurantProfile.objects.get(user=request.user, is_approved=False)
    except RestaurantProfile.DoesNotExist:
        restaurant = None


    if request.method == "POST":
        form = RestaurantProfileForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.user_type = 'restaurant'
            restaurant.user = request.user
            restaurant.is_approved = False
            restaurant.save()
            name = form.cleaned_data.get('restaurant_name')
            messages.success(request, f"Restaurant request sent")
            return redirect('restaurant-register')
        else:
            messages.error(request, "Invalid inputs.")
    else:
        form = RestaurantProfileForm(instance=restaurant)

    context = {'form': form, 'restaurant': restaurant,
               'restaurant_registration':True}

    return render(request, './restaurant/restaurant-register.html', context)  

@login_required(login_url='login')
def profile(request):
    restaurant = get_object_or_404(RestaurantProfile, user=request.user)
    
    if request.method == "POST":
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.user_type = 'restaurant'
            restaurant.user = request.user
            restaurant.is_approved = False
            restaurant.save()
            messages.success(request, "Restaurant profile updated.")
            return redirect('restaurant-profile')
        else:
            messages.error(request, "Invalid inputs.")
    else:
        form = RestaurantProfileForm(instance=restaurant)
    
    context = {'form': form, 'restaurant_obj': restaurant}
    return render(request, './restaurant/restaurant-profile.html', context)



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
    if request.user.user_type != 'restaurant':
        messages.error(request, "Not restaurant user")
        return redirect('login')
    restaurant = get_object_or_404(RestaurantProfile, user=request.user)
    subscriptions = Subscriptions.objects.filter(restaurant=restaurant, user__isnull=False)
    paginator = Paginator(subscriptions, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj
    }
    return render(request, './restaurant/all_users.html', context)


@login_required(login_url='admin-login')
def orders(request):
    user = request.user
    restaurant = get_object_or_404(RestaurantProfile, user=request.user)
    sort_by = request.GET.get('sort', 'delivery_date')  # default: delivery_date
    direction = request.GET.get('dir', 'asc') 
    order_prefix = '' if direction == 'asc' else '-'
    valid_sort_fields = ['delivery_date', 'status']
    sort_field = sort_by if sort_by in valid_sort_fields else 'delivery_date'
    orders = Orders.objects.filter(restaurant=restaurant).order_by(f"{order_prefix}{sort_field}")
    user = request.GET.get('user')
    status = request.GET.get('status')
    delivery_date = request.GET.get('delivery_date')


    if user:
        orders = orders.filter(user__username__icontains=user)

    if status:
        orders = orders.filter(status=status)

    if delivery_date:
        orders = orders.filter(delivery_date=delivery_date)

    paginator = Paginator(orders, 10)  # Show 5 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    print(f"{orders=}")
    context = {'orders': page_obj,
                'sort': sort_field,
                'dir': direction,
                
                }
    return render(request, './restaurant/orders.html', context)


@login_required
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Orders, id=order_id)

        if order.cancel():
            messages.success(request, f"Order cancelled successfully")
        else:
            messages.error(request, "Order cannot be cancelled.")
    except Exception as e:
        print(f"{e=}")
        messages.error(request,"Server error")
    finally:
        return redirect('restaurant-orders')
    
@login_required(login_url='admin-login')
def deliver_order(request, order_id):
    print("Delivering order")
    try:
        order = get_object_or_404(Orders, id=order_id)
        order.status = "DELIVERED"
        order.save()
        messages.success(request, f"Order Delivered")
    except Exception as e:
        print(f"{e=}")
        messages.error(request,"Server error")
    finally:
        return redirect('restaurant-orders')





@login_required(login_url='login')
def foods(request):

    if request.user.user_type != 'restaurant':
        messages.error(request, "Not restaurant user")
        return redirect('login')

    user = request.user
    restaurant = get_object_or_404(RestaurantProfile, user=request.user)
    foods = FoodItem.objects.filter(restaurant=restaurant).order_by('-created_at')
    paginator = Paginator(foods, 10)  # Show 5 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'foods': page_obj,
        'orders':page_obj
    }
    return render(request, './restaurant/food_items.html', context)


@login_required()
def food_add_or_update(request, pk=None):
    if request.user.user_type != 'restaurant':
        messages.error(request, "Not restaurant user")
        return redirect('login')
    if pk:
        food_obj = get_object_or_404(FoodItem, pk=pk)
    else:
        food_obj = None

    restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)


    if request.method == "POST":
        form = FoodItemManageForm(request.POST, request.FILES, instance=food_obj)
        if form.is_valid():
            restaurant_form = form.save(commit=False)
            restaurant_form.restaurant = restaurant_obj
            restaurant_form.save()
            messages.success(request, f"Food  {'Updated' if pk else 'Created'} ")
            return redirect('restaurant-food_items')
        else:
            messages.error(request, "Invalid inputs.")
            print(form.errors)
    else:
        form = FoodItemManageForm(instance=food_obj)


    return render(request, './restaurant/add-food.html', {'form': form})


@login_required(login_url='login')
def delete_food_item(request, id):
    if request.user.user_type != 'restaurant':
        messages.error(request, "Not restaurant user")
        return redirect('login')
    food = get_object_or_404(FoodItem, pk=id)
    food.delete()
    return redirect('restaurant-food_items')



@login_required(login_url='login')
def menus(request):
    restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)
    menus = MenuCategory.objects.filter(restaurant=restaurant_obj).order_by('-created_at')
    context = {
        'menus': menus
    }
    return render(request, './restaurant/menus.html', context)


def menu_add_or_update(request, pk=None):
    if pk:
        menu_obj = get_object_or_404(MenuCategory, pk=pk)
    else:
        menu_obj = None
    restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)


    if request.method == "POST":
        form = MenuManageForm(request.POST, request.FILES, instance=menu_obj)
        if form.is_valid():
            menu = form.save(commit=False)
            menu.restaurant = restaurant_obj
            menu.save()
            messages.success(request, f"Menu  {'Updated' if pk else 'Created'} ")
            return redirect('restaurant-menu_items')
        else:
            messages.error(request, "Invalid inputs.")
    else:
        form = MenuManageForm(instance=menu_obj)


    return render(request, './restaurant/add-menu.html', {'form': form})


def menu_food_item(request, id):
    menu = get_object_or_404(MenuCategory, pk=id)
    menu.delete()
    return redirect('restaurant-menu_items')





@login_required(login_url='admin-login')
def food_category(request):


    foods = FoodCategory.objects.all().order_by('-created_at')
    context = {
        'foods': foods
    }
    return render(request, './restaurant/food_categories.html', context)


def category_add_or_update(request, pk=None):
    if pk:
        food_obj = get_object_or_404(FoodCategory, pk=pk)
    else:
        food_obj = None
    restaurant_obj = get_object_or_404(RestaurantProfile, user=request.user)


    if request.method == "POST":
        form = FoodCategoryManageForm(request.POST, request.FILES, instance=food_obj)
        if form.is_valid():
            restaurant_form = form.save(commit=False)
            restaurant_form.restaurant = restaurant_obj
            restaurant_form.save()
            messages.success(request, f"Category  {'Updated' if pk else 'Created'} ")
            return redirect('restaurant-food_category')
        else:
            messages.error(request, "Invalid inputs.")
    else:
        form = FoodCategoryManageForm(instance=food_obj)


    return render(request, './restaurant/add-category.html', {'form': form})


def delete_food_category(request, id):
    food = get_object_or_404(FoodCategory, pk=id)
    food.delete()
    return redirect('restaurant-food_category')
