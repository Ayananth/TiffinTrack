from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import AdminUserRegisterForm, UserUpdateForm, RestaurantRegisterForm, FoodItemManageForm, MenuManageForm, FoodCategoryManageForm
from accounts.models import CustomUser
from django.views.decorators.cache import never_cache
from restaurant.models import RestaurantProfile, FoodItem, MenuCategory, FoodCategory, Subscriptions
from django.core.paginator import Paginator
from users.models import Orders, RestaurantReport
from django.utils.timezone import now
from django.utils.timezone import localtime
from datetime import datetime
from coupons.models import Coupon

from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from datetime import date





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
    if not request.user.is_superuser:
        return redirect('admin-login')
    today = date.today()
    start_date = today.replace(day=1)
    end_date = today
    start_date = request.GET.get('start_date', start_date)
    end_date = request.GET.get('end_date', end_date)
    if isinstance(start_date, str):
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()

    print(f"{start_date=}")
    print(f"{end_date=}")

    orders = Orders.objects.filter(delivery_date__range=(start_date, end_date))
    print(f"{orders.values()=}")
    total_orders = orders.count()
    total_revenue = orders.filter(status='DELIVERED').aggregate(
        revenue=Sum('food_category__price'))['revenue'] or 0
    total_subscriptions = Subscriptions.objects.filter(
        created_at__date__range=(start_date, end_date)
    ).count()
    active_restaurants = RestaurantProfile.objects.filter(received_orders__delivery_date__range=(start_date, end_date)).distinct().count()
    most_ordered_restaurant = orders.values(
        'restaurant__restaurant_name'
    ).annotate(count=Count('id')).order_by('-count').first()

    top_restaurants = orders.filter(status='DELIVERED').values(
        'restaurant__id',
        'restaurant__restaurant_name',
    ).annotate(
        revenue=Sum('food_category__price')
    ).order_by('-revenue')[:3]

    print(f"{top_restaurants=}")

    total_orders = Orders.objects.count()
    pending_orders = Orders.objects.filter(status='PENDING').count()
    delivered_orders = Orders.objects.filter(status='DELIVERED').count()
    cancelled_orders = Orders.objects.filter(status='CANCELLED').count()

    # For chart
    order_status_labels = ['Pending', 'Delivered', 'Cancelled']
    order_status_data = [pending_orders, delivered_orders, cancelled_orders]

    

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_subscriptions': total_subscriptions,
        'active_restaurants': active_restaurants,
        'most_ordered_restaurant': most_ordered_restaurant['restaurant__restaurant_name'] if most_ordered_restaurant else "N/A",
        'top_restaurant_by_revenue': top_restaurants[0]['restaurant__restaurant_name'] if top_restaurants else "N/A",
        'top_restaurants': top_restaurants,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'order_status_labels': order_status_labels,
        'order_status_data': order_status_data,
    }

    chart_labels = [item['restaurant__restaurant_name'] for item in top_restaurants]
    chart_data = [float(item['revenue']) for item in top_restaurants]

    context.update({
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })

    print(f"{context=}")

    return render(request, './admin_panel/dashboard.html', context)


@login_required(login_url='admin-login')
def all_users(request):
    if not request.user.is_superuser:
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
    if not request.user.is_superuser:
        return redirect('admin-login')
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
    if not request.user.is_superuser:
        return redirect('admin-login')
    

    restaurants = RestaurantProfile.objects.all().order_by('is_approved','-created_at')
    paginator = Paginator(restaurants, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'restaurants': page_obj
    }
    return render(request, './admin_panel/restaurants.html', context)


@never_cache
@login_required(login_url='admin-login')
def restaurant_requests(request):
    if not request.user.is_superuser:
        return redirect('admin-login')

    restaurants = RestaurantProfile.objects.filter(is_approved=False)
    context = {
        'restaurants': restaurants
    }
    return render(request, './admin_panel/register_restaurant.html', context)


def restaurant_add_or_update(request, pk=None):
    if not request.user.is_superuser:
        return redirect('admin-login')
    if pk:
        restaurant_obj = get_object_or_404(RestaurantProfile, pk=pk)
    else:
        restaurant_obj = None

    food_items = [] 

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

    if restaurant_obj:
        food_items = FoodItem.objects.select_related('menu_category').filter(restaurant=restaurant_obj)

    return render(request, './admin_panel/add-restaurant.html', {
        'form': form,
        'food_items': food_items
    })


def restaurant_dashboard(request, pk=None):
    if not request.user.is_superuser:
        return redirect('admin-login')
    today = '2025-05-19'
    # selected_date = localtime().date()
    # today = selected_date
    selected_date = today
    print(today)
    restaurant = get_object_or_404(RestaurantProfile, pk=pk)

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



 
    return render(request, './admin_panel/restaurant-dashboard.html', context)

    

@login_required(login_url='admin-login')
def restaurant_approve(request, pk):
    if not request.user.is_superuser:
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
    if not request.user.is_superuser:
        return redirect('admin-login')
    restaurant = get_object_or_404(RestaurantProfile, pk=id)
    restaurant.delete()
    return redirect('restaurants')

@never_cache
@login_required(login_url='admin-login')
def delete_user(request, id):
    if not request.user.is_superuser:
        return redirect('admin-login')
    user = get_object_or_404(CustomUser, pk=id)
    user.delete()
    messages.success(request,"User deleted")
    return redirect('all-users')




@never_cache
@login_required(login_url='admin-login')
def update_user(request, id):
    if not request.user.is_superuser:
        return redirect('admin-login')
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





# Food Items

@login_required(login_url='admin-login')
def foods(request):

    if not request.user.is_superuser:
        return redirect('admin-login')

    foods = FoodItem.objects.all().order_by('-created_at')
    paginator = Paginator(foods, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'foods': page_obj
    }
    return render(request, './admin_panel/food_items.html', context)


# menu Items

@login_required(login_url='admin-login')
def menus(request):
    if not request.user.is_superuser:
        return redirect('admin-login')

    menus = MenuCategory.objects.all().order_by('-created_at')
    paginator = Paginator(menus, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'menus': page_obj
    }
    return render(request, './admin_panel/menus.html', context)


@login_required()
def menu_add_or_update(request, pk=None):
    if pk:
        menu_obj = get_object_or_404(MenuCategory, pk=pk)
    else:
        menu_obj = None

    if request.method == "POST":
        form = MenuManageForm(request.POST, request.FILES, instance=menu_obj)
        if form.is_valid():
            menu = form.save()
            messages.success(request, f"Menu  {'Updated' if pk else 'Created'} ")
            return redirect('menu_items')
        else:
            messages.error(request, "Invalid inputs.")
    else:
        form = MenuManageForm(instance=menu_obj)


    return render(request, './admin_panel/add-menu.html', {'form': form})


@login_required(login_url='admin-login')
def menu_food_item(request, id):
    menu = get_object_or_404(MenuCategory, pk=id)
    menu.delete()
    return redirect('menu_items')






# Food category

@login_required(login_url='admin-login')
def food_category(request):
    if not request.user.is_superuser:
        return redirect('admin-login')

    foods = FoodCategory.objects.all().order_by('-created_at')
    paginator = Paginator(foods, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'foods': page_obj
    }
    return render(request, './admin_panel/food_categories.html', context)


@login_required()
def category_add_or_update(request, pk=None):
    if pk:
        food_obj = get_object_or_404(FoodCategory, pk=pk)
    else:
        food_obj = None

    if request.method == "POST":
        form = FoodCategoryManageForm(request.POST, request.FILES, instance=food_obj)
        if form.is_valid():
            restaurant = form.save()
            messages.success(request, f"Category  {'Updated' if pk else 'Created'} ")
            return redirect('food_category')
        else:
            messages.error(request, "Invalid inputs.")
    else:
        form = FoodCategoryManageForm(instance=food_obj)


    return render(request, './admin_panel/add-category.html', {'form': form})


@login_required(login_url='admin-login')
def delete_food_category(request, id):
    food = get_object_or_404(FoodCategory, pk=id)
    food.delete()
    return redirect('food_category')


@login_required(login_url='admin-login')
def orders(request):
    user = request.user

    sort_by = request.GET.get('sort', 'delivery_date')  # default: delivery_date
    direction = request.GET.get('dir', 'asc') 
    order_prefix = '' if direction == 'asc' else '-'
    valid_sort_fields = ['delivery_date', 'status']
    sort_field = sort_by if sort_by in valid_sort_fields else 'delivery_date'

    orders = Orders.objects.all().order_by(f"{order_prefix}{sort_field}")

    restaurant = request.GET.get('restaurant')
    user = request.GET.get('user')
    status = request.GET.get('status')
    delivery_date = request.GET.get('delivery_date')

    if restaurant:
        orders = orders.filter(restaurant__restaurant_name__icontains=restaurant)

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
    return render(request, './admin_panel/orders.html', context)


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
        return redirect('admin-orders')
    
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
        return redirect('admin-orders')
    


@login_required(login_url='admin-login')
def coupons(request):
    user = request.user

    sort_by = request.GET.get('sort', 'delivery_date')  # default: delivery_date
    direction = request.GET.get('dir', 'asc') 
    order_prefix = '' if direction == 'asc' else '-'
    valid_sort_fields = ['delivery_date', 'status']
    sort_field = sort_by if sort_by in valid_sort_fields else 'delivery_date'

    coupons = Coupon.objects.all().order_by('-created_at')

    restaurant = request.GET.get('restaurant')
    user = request.GET.get('user')
    status = request.GET.get('status')
    delivery_date = request.GET.get('delivery_date')



    paginator = Paginator(coupons, 10)  # Show 5 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    print(f"{orders=}")
    context = {'coupons': page_obj,
                'sort': sort_field,
                'dir': direction,
                
                }
    return render(request, './admin_panel/coupon.html', context)






def sales_report_overview(request):
    today = date.today()
    start_date = today.replace(day=1)
    end_date = today
    start_date = request.GET.get('start_date', start_date)
    end_date = request.GET.get('end_date', end_date)
    if isinstance(start_date, str):
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
    orders = Orders.objects.filter(delivery_date__range=(start_date, end_date))
    total_orders = orders.count()
    total_revenue = orders.filter(status='DELIVERED').aggregate(
        revenue=Sum('food_category__price'))['revenue'] or 0
    total_subscriptions = Subscriptions.objects.filter(
        created_at__date__range=(start_date, end_date)
    ).count()
    active_restaurants = RestaurantProfile.objects.filter(received_orders__delivery_date__range=(start_date, end_date)).distinct().count()
    most_ordered_item = orders.values('food_item__name').annotate(
        count=Count('id')).order_by('-count').first()
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_subscriptions': total_subscriptions,
        'active_restaurants': active_restaurants,
        'most_ordered_item': most_ordered_item['food_item__name'] if most_ordered_item else "N/A",
    }

    return render(request, './admin_panel/dashboard.html', context)


@login_required(login_url='admin-login')
def report_restaurant(request):
    user = request.user



    restaurant = request.GET.get('restaurant')
    user = request.GET.get('user')
    status = request.GET.get('status')
    created = request.GET.get('created')



    reports = RestaurantReport.objects.all()



    paginator = Paginator(reports, 10)  # Show 5 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    print(f"{orders=}")
    context = {'reports': page_obj,
                }
    return render(request, './admin_panel/report.html', context)



@login_required(login_url='admin-login')
def delete_report(request, id):
    if not request.user.is_superuser:
        return redirect('admin-login')
    report = get_object_or_404(RestaurantReport, id=id)
    report.delete()
    messages.success(request, "report deleted successfully.")
    return redirect('admin-report-restaurant')

