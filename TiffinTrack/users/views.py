from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from accounts.forms import UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from restaurant.models import RestaurantProfile, FoodItem, FoodCategory, MenuCategory, Subscriptions
from accounts.models import UserProfile, Locations
from django.db.models import Avg
from collections import defaultdict
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D  # D for Distance
from django.contrib.gis.db.models.functions import Distance
from accounts.utils import get_location_from_point
from django.core.paginator import Paginator
from datetime import timedelta





from .models import Address, Orders
from .forms import AddressForm, SubscriptionForm





@login_required(login_url='login')
def home(request):
    print(request.user)
    user = request.user
    restaurant_name = request.GET.get('restaurant_name')
    print(user.profile.point)
    reference_point = user.profile.point
    longitude = reference_point.x
    latitude = reference_point.y
    location_name = get_location_from_point(longitude, latitude)

    # Filter restaurants within 20 km
    nearby_restaurants= RestaurantProfile.objects.annotate(
        distance=Distance('point', reference_point)
    ).filter(
        distance__lte=D(km=20)
    ).order_by('distance')


    queryset = RestaurantProfile.objects.filter(is_approved=True)
    if restaurant_name:
        queryset = queryset.filter(restaurant_name__icontains=restaurant_name.strip())


    # Apply distance annotation and filter
    restaurants = queryset.annotate(
        distance=Distance('point', reference_point),
        avg_rating=Avg('reviews__rating')
    ).filter(
        distance__lte=D(km=20)
    ).order_by('distance')

    paginator = Paginator(restaurants, 12)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)



    # menu = get_object_or_404(MenuCategory, id=1)
    # food_categories = menu.food_categories.all()
    # print(f"{food_categories=}")




    context = {
        'restaurants': page_obj,
        'location': location_name
    }

    return render(request, './users/home.html', context)


@login_required(login_url='login')
def update_profile(request):
    user = request.user
    profile = user.profile
    email = user.email

    reference_point = user.profile.point
    longitude = reference_point.x
    latitude = reference_point.y
    location = get_location_from_point(longitude, latitude)
    print("test")

    user_form = UserUpdateForm(instance=user)
    print(f"{user.profile=}")
    profile_form = ProfileUpdateForm(instance=user.profile)

    if request.method == 'POST':
        print("POST request received")
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            print("Forms are valid")
            user_form_instance = user_form.save(commit=False)
            user_form_instance.email = email 
            user_form_instance.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('user-profile')  # Redirect to a profile page after saving
        else:
            print("Forms are not valid")
            print(user_form.errors)
            print(profile_form.errors)
            messages.error(request, "Error updating profile. Please check the form.")

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'location' : location,
    })


@login_required(login_url='login')
def update_user_location(request):
    print(request.POST)
    print("update_user_location")
    latitude = float(request.POST.get("latitude"))
    longitude = float(request.POST.get("longitude"))
    point = Point(longitude, latitude)
    profile = request.user.profile
    profile.point = point
    profile.save()
    return redirect('user-home')


@login_required(login_url='login')
def manage_user_address(request, id=None):
    user=request.user
    addresses = Address.objects.filter(user=user)

    address_instance = None
    if id is not None:
        address_instance = get_object_or_404(Address, id=id, user=user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address_instance)
        if form.is_valid():
            data = form.save(commit=False)
            data.user = user
            data.save()
            messages.success(request, "Success")
            return redirect('address')
        else:
            messages.error(request,"Invalid Inputs")
    else:
        form = AddressForm(instance=address_instance)

    context = {"addresses": addresses, 'form': form,
                "editing": id is not None,
                "address_id": id,}
    return render(request, 'users/address.html', context)



    



def restaurant_details(request, pk):

    restaurant = get_object_or_404(RestaurantProfile, pk=pk)
    avg_rating = restaurant.reviews.aggregate(Avg('rating'))['rating__avg']
    reviews = restaurant.reviews.all().count()
    menu_categories = MenuCategory.objects.filter(is_active=True)
    print(f"{menu_categories=}")
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    menu_data = []


    for menu_category in menu_categories:
        category_prices = {}
        food_categories = FoodCategory.objects.filter(menu_categories=menu_category, is_active=True)
        print(f"{food_categories=}")

        weekly_menu = defaultdict(lambda: {str(meal): [] for meal in food_categories})
        print(f"{weekly_menu=}")


        # Get all food items for this menu category
        food_items = FoodItem.objects.filter(menu_category=menu_category, is_available=True)

        # Get prices for only those food categories that belong to this menu
        for food_cat in food_categories:
            category_prices[food_cat.name] = food_cat.price
            print(f"Category: {food_cat.name}, Price: {food_cat.price}")

        for item in food_items:
            # Only include items with both a food_category and a day
            if item.food_category and item.day:
                weekly_menu[item.day][item.food_category.name].append(item.name)

        # Sort the weekly menu based on day order
        sorted_menu = {day: weekly_menu[day] for day in days_order}

        start_end_time = {}

        for food_cat in food_categories:
            start_end_time[food_cat.name] = {'start_time': food_cat.start_time,
                                             'end_time': food_cat.end_time,
                                             'cancellation_time': food_cat.cancellation_time}

        print(f"{start_end_time=}")


        

        total_price = sum(category_prices.values())
        menu_data.append({
            'menu_category': menu_category.name,
            'weekly_menu': sorted_menu,
            'category_prices': category_prices,
            'total_price': total_price,
            'food_categories': food_categories,
            'start_end_time': start_end_time,
            'menu_description': menu_category.description,
            'menu_id': menu_category.id
            
        })




    context = {
        'restaurant': restaurant,
        'rating': avg_rating,
        'reviews': reviews,
        'location': restaurant.location_name,
         'menu_data': menu_data,

        
    }

    print(f"{context=}")
    return render(request, 'users/restaurant_detail.html', context)
    
    
    



@login_required(login_url='login')
def subscription_cart(request, id=None):
    print("subscription page")
    print(f"{id=}")


    user = request.user
    addresses = Address.objects.filter(user=user)
    menu = get_object_or_404(MenuCategory, id=id)
    print(f"{menu=}")


    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            print("form valid")
            subscription = form.save(commit=False)
            print("-----------------------")
            print(Subscriptions.objects.filter(user=user, is_active=True))
            if Subscriptions.objects.filter(user=user, is_active=True).exists():
                print("subscription Already exists")
                messages.error(request, "You already have a subscription")
                return redirect('subscription-request', id=id)
            print("No existing subscription")
            subscription.restaurant = menu.restaurant
            subscription.menu_category = menu
            number_of_days = form.cleaned_data.get('end_date') - form.cleaned_data.get('start_date')
            print(f"{number_of_days=}")
            subscription.per_day_amount = menu.total_price
            subscription.total_amount = number_of_days.days * menu.total_price
            subscription.num_days = number_of_days.days
            subscription.save()


            start_date = subscription.start_date.date()
            end_date = subscription.end_date.date()

            food_categories = menu.food_categories.all()
            print(f"{food_categories=}")


            orders_to_create = []
            current_date = start_date
            while current_date <= end_date:
                for food_category in food_categories:
                    orders_to_create.append(Orders(
                        user=user,
                        restaurant=subscription.restaurant,
                        food_category=food_category,
                        food_item=None,  # You can assign a default item here if needed
                        delivery_date=current_date,
                        status='PENDING'
                    ))
                current_date += timedelta(days=1)
            print(f"{orders_to_create=}")
            # Create all orders at once
            Orders.objects.bulk_create(orders_to_create)



            return redirect('payment', id=subscription.id)
        else:
            messages.error(request, "Form not valid")
            print("Form not valid")
    else:
        form = SubscriptionForm()


    context = {'addresses': addresses,  'form': form}
    print(f"{context=}")
    return render(request, 'users/subscription_request.html', context)
    





@login_required(login_url='login')
def order_confirm(request):
    return render(request, 'users/success.html')


@login_required(login_url='login')
def payment(request, id):
    subscription = get_object_or_404(Subscriptions, id=id)
    if request.method == 'POST':
        paid_amount = request.POST.get('paid_amount',0)
        subscription.paid_total_amount = paid_amount
        subscription.user = request.user
        subscription.is_active =  True
        subscription.save()
        return redirect('order-confirm')
    context = {'subscription': subscription}
    
    return render(request, 'users/payment.html', context)
    

@login_required(login_url='login')
def orders(request):
    user = request.user

    sort_by = request.GET.get('sort', 'delivery_date')  # default: delivery_date
    direction = request.GET.get('dir', 'asc') 
    order_prefix = '' if direction == 'asc' else '-'
    valid_sort_fields = ['delivery_date', 'status']
    sort_field = sort_by if sort_by in valid_sort_fields else 'delivery_date'

    orders = Orders.objects.filter(user=user).order_by(f"{order_prefix}{sort_field}")


    paginator = Paginator(orders, 10)  # Show 5 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    #wallet balance
    wallet = getattr(request.user, 'wallet', None)
    wallet_balance = wallet.balance if wallet else 0



    print(f"{orders=}")
    context = {'orders': page_obj,
               'title':"Orders",
                'sort': sort_field,
                'dir': direction,
                'wallet_balance': wallet_balance,}
    return render(request, './users/orders.html', context)


@login_required
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Orders, id=order_id, user=request.user)

        if order.cancel():
            messages.success(request, f"Order cancelled successfully.  ₹{order.food_category.price} refunded to your wallet.")
        else:
            messages.error(request, "Order cannot be cancelled.")
    except:
        messages.error(request,"Server errir")
    finally:
        return redirect('orders')
    


@login_required(login_url='login')
def wallet(request):
    wallet = request.user.wallet  # OneToOne relation
    transactions = wallet.transactions.order_by('-created_at')  # Most recent first

    paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'balance': wallet.balance,
        'title': "Wallet Transactions"
    }
    return render(request, './users/wallet.html', context)