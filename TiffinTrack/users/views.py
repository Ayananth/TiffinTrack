from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from accounts.forms import UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from restaurant.models import RestaurantProfile, FoodItem, FoodCategory, MenuCategory, Subscriptions
from accounts.models import UserProfile, Locations
from django.db.models import Avg, Max
from collections import defaultdict
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D  # D for Distance
from django.contrib.gis.db.models.functions import Distance
from accounts.utils import get_location_from_point
from django.core.paginator import Paginator
from datetime import timedelta
from datetime import datetime
from django.http import Http404








from .models import Address, Orders, Wallet
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

    reference_point = user.profile.point
    longitude = reference_point.x
    latitude = reference_point.y
    location = get_location_from_point(longitude, latitude)

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
                "address_id": id,
                "location":location}
    return render(request, 'users/address.html', context)



    



from collections import defaultdict
@login_required(login_url='login')
def restaurant_details(request, pk):
    restaurant = get_object_or_404(RestaurantProfile, pk=pk)

    # Restaurant summary
    avg_rating = restaurant.reviews.aggregate(Avg('rating'))['rating__avg']
    reviews_count = restaurant.reviews.count()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Get active menu categories
    menu_categories = MenuCategory.objects.filter(is_active=True, restaurant=restaurant)
    menu_data = []

    for menu_category in menu_categories:
        # Get active food categories linked to this menu category and restaurant
        food_categories = FoodCategory.objects.filter(
            menu_category=menu_category,
            restaurant=restaurant,
            is_active=True
        )

        # Initialize weekly menu with empty lists for each category per day
        weekly_menu = defaultdict(lambda: {fc.name: [] for fc in food_categories})

        # Get available food items in this menu category
        food_items = FoodItem.objects.filter(menu_category=menu_category, is_available=True)

        # Category price and timing info
        category_prices = {}
        start_end_time = {}

        for food_cat in food_categories:
            category_prices[food_cat.name] = food_cat.price
            start_end_time[food_cat.name] = {
                'start_time': food_cat.start_time,
                'end_time': food_cat.end_time,
                'cancellation_time': food_cat.cancellation_time,
            }

        # Populate weekly_menu with food item names
        for item in food_items:
            if item.food_category and item.day:
                day = item.day
                category_name = item.food_category.name
                if category_name in weekly_menu[day]:  # Prevent KeyError
                    weekly_menu[day][category_name].append(item.name)

        # Sort weekly_menu by day order
        sorted_menu = {day: weekly_menu.get(day, {}) for day in days_order}

        # Append structured data for template
        menu_data.append({
            'menu_category': menu_category.name,
            'menu_description': menu_category.description,
            'menu_id': menu_category.id,
            'weekly_menu': sorted_menu,
            'category_prices': category_prices,
            'total_price': sum(category_prices.values()),
            'food_categories': food_categories,
            'start_end_time': start_end_time,
        })

    context = {
        'restaurant': restaurant,
        'rating': avg_rating,
        'reviews': reviews_count,
        'location': restaurant.location_name,
        'menu_data': menu_data,
    }

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
            end_date = request.POST.get('end_date')
            print("-----------------------")

            start_date = subscription.start_date

            # Check if any existing subscription for the user ends before the new subscription starts
            overlapping_subscriptions = Subscriptions.objects.filter(
                user=user,
                end_date__gte=start_date,
                is_active = True
            )
            if overlapping_subscriptions.exists():
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
            subscription.address = form.cleaned_data.get('address')
            subscription.save()


            # start_date = subscription.start_date.date()
            # end_date = subscription.end_date.date()

            # food_categories = menu.food_categories.all()
            # print(f"{food_categories=}")


            # orders_to_create = []
            # current_date = start_date
            # while current_date <= end_date:
            #     for food_category in food_categories:
            #         orders_to_create.append(Orders(
            #             user=user,
            #             restaurant=subscription.restaurant,
            #             food_category=food_category,
            #             food_item=None,  # You can assign a default item here if needed
            #             delivery_date=current_date,
            #             status='PENDING',
            #             address = subscription.address

            #         ))
            #     current_date += timedelta(days=1)
            # print(f"{orders_to_create=}")
            # # Create all orders at once
            # Orders.objects.bulk_create(orders_to_create)



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



    #Place orders
    subscription = request.session.get('subscription')
    if not subscription:
        messages.error("Session expired, Please try again")
        return redirect('home')
    subscription = get_object_or_404(Subscriptions, id=subscription)    
    start_date = subscription.start_date.date()
    end_date = subscription.end_date.date()
    menu = subscription.menu_category
    food_categories = menu.food_categories.all()
    print(f"{food_categories=}")
    orders_to_create = []
    current_date = start_date
    while current_date <= end_date:
        for food_category in food_categories:
            orders_to_create.append(Orders(
                user=request.user,
                restaurant=subscription.restaurant,
                food_category=food_category,
                food_item=None,  # You can assign a default item here if needed
                delivery_date=current_date,
                status='PENDING',
                address = subscription.address

            ))
        current_date += timedelta(days=1)
    print(f"{orders_to_create=}")
    # Create all orders at once
    Orders.objects.bulk_create(orders_to_create)

    wallet_amount = request.POST.get('wallet_amount')

    if wallet_amount:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.debit(int(wallet_amount), description=f"Used for subscription")

    del request.session['subscription']


    return render(request, 'users/success.html')


@login_required(login_url='login')
def payment(request, id):
    wallet = request.user.wallet.balance
    try:
        subscription = get_object_or_404(Subscriptions, id=id)
    except Http404:
        messages.error(request, "Bad request")
        return redirect('user-home')
    if request.method == 'POST':

        #TODO check if already have a subscription
        paid_amount = request.POST.get('paid_amount',0)
        print(f"{paid_amount=}")
        subscription.paid_total_amount = paid_amount
        subscription.user = request.user
        # subscription.is_active =  True
        subscription.save()
        request.session['subscription'] = subscription.id

        if paid_amount!=0:
            return redirect('initiate_payment')
        else:
            return redirect('order-confirm')
        




        #Place orders
        start_date = subscription.start_date.date()
        end_date = subscription.end_date.date()
        menu = subscription.menu_category
        food_categories = menu.food_categories.all()
        print(f"{food_categories=}")


        orders_to_create = []
        current_date = start_date
        while current_date <= end_date:
            for food_category in food_categories:
                orders_to_create.append(Orders(
                    user=request.user,
                    restaurant=subscription.restaurant,
                    food_category=food_category,
                    food_item=None,  # You can assign a default item here if needed
                    delivery_date=current_date,
                    status='PENDING',
                    address = subscription.address

                ))
            current_date += timedelta(days=1)
        print(f"{orders_to_create=}")
        # Create all orders at once
        Orders.objects.bulk_create(orders_to_create)

        wallet_amount = request.POST.get('wallet_amount')

        if wallet_amount:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            wallet.debit(int(wallet_amount), description=f"Used for subscription")

            
        return redirect('order-confirm')
    
    context = {'subscription': subscription,
               'wallet_amount': wallet}
    
    return render(request, 'users/payment.html', context)


@login_required(login_url='login')
@require_POST
def use_wallet(request):
    id = request.POST.get('subscription_id')
    subscription_id = request.POST.get('subscription_id')
    try:
        subscription = Subscriptions.objects.get(id=subscription_id, user=request.user)
    except Subscriptions.DoesNotExist:
        messages.error(request, "Please try again! ")
        return redirect('user-home')
    wallet_balance = request.user.wallet.balance
    original_total = subscription.final_total
    final_total = original_total
    if wallet_balance >= final_total:
        wallet_used = final_total
        final_total = 0
    else:
        wallet_used = wallet_balance
        final_total = final_total - wallet_used
    
    subscription.wallet_amount_used = wallet_used
    subscription.save()
    return redirect('payment', id=subscription_id)


@login_required(login_url='login')
@require_POST
def remove_wallet(request):
    subscription_id = request.POST.get('subscription_id')
    try:
        subscription = Subscriptions.objects.get(id=subscription_id, user=request.user)
    except Subscriptions.DoesNotExist:
        messages.error(request, "Please try again! ")
        return redirect('payment', id=subscription_id)

    subscription.wallet_amount_used = 0.00
    subscription.save()
    return redirect('payment', id=subscription_id)





@login_required(login_url='login')
def manage_subscription(request):
    user = request.user
    headers = [
        {'url': 'user-profile', 'name': 'Profile' },
        {'url': 'manage_subscription', 'name': 'Manage Subscription' },
    ]

    if request.method == 'POST':
        print("post requesttasdf")
        print(request.POST)
        id = request.POST.get('subscription_id')
        print(id)
        if id:
            print(id)
            subscription = get_object_or_404(Subscriptions, id=id)
            print(f"{subscription=}")
            subscription.is_active = False
            subscription.save()
            orders = subscription.orders.filter(status='PENDING')
            print(f"{orders=}")
            for order in orders:
                order.cancel()
            messages.success(request,"Your subscription and orders are cancelled")
            context = {
                'headers': headers
            }
            return render(request, './users/manage_subscription.html', context)

    subscription = user.subscriptions.filter(is_active=True).first()
    if not subscription:
        context = {
            'headers': headers,
            'message': "No active subscription found.",
        }
        return render(request, 'users/manage_subscription.html', context)
    food_categories = FoodCategory.objects.filter(menu_category=subscription.menu_category)
    orders = subscription.orders.all()
    # format:
    # delivery_data = {
    #     'breakfast': {
    #         'delivered': 5,
    #         'ordered': 5,
    #         'remaining': 5
    #     },
    #     'lunch': {
    #         'delivered': 5,
    #         'ordered': 5,
    #         'remaining': 5
    #     },

    # }

    refund = 0

    delivery_data = {}
    for food_category in food_categories:
        data = {}
        data['delivered'] = orders.filter(food_category=food_category, status='DELIVERED').count()
        data['cancelled'] = orders.filter(food_category=food_category, status='CANCELLED').count()
        pending = orders.filter(food_category=food_category, status='PENDING').count()
        data['pending'] = pending
        refund += pending * food_category.price
        delivery_data[food_category] = data
    
    print(f"{delivery_data=}")

    context = {
        'headers': headers,
        'subscription':subscription,
        'delivery_data': delivery_data,
        'refund' : refund
    }
    return render(request, './users/manage_subscription.html', context)
    

@login_required(login_url='login')
def orders(request):
    user = request.user
    reference_point = user.profile.point
    longitude = reference_point.x
    latitude = reference_point.y
    location = get_location_from_point(longitude, latitude)

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
                'wallet_balance': wallet_balance,
                'location': location}
    return render(request, './users/orders.html', context)


@login_required
def cancel_order(request, order_id):
    print("Order cancellation")
    try:
        order = get_object_or_404(Orders, id=order_id, user=request.user)
        now = timezone.now()
        cancellation_datetime = datetime.combine(now.date(), order.food_category.cancellation_time)
        cancellation_datetime = timezone.make_aware(cancellation_datetime, timezone.get_current_timezone())
        print(f"{now=}")
        print(f"{cancellation_datetime=}")

        if now > cancellation_datetime:
            messages.error(request, "Late for order cancellation")
            return redirect('orders')
        if order.cancel():
            messages.success(request, f"Order cancelled successfully.  ₹{order.food_category.price} refunded to your wallet.")
        else:
            messages.error(request, "Order cannot be cancelled.")
    except Exception as e:
        print(f"{e=}")
        messages.error(request,"Server error")
    finally:
        return redirect('orders')
    

@login_required
def extend_subscription(request, order_id):
    print("Order cancellation")
    try:
        order = get_object_or_404(Orders, id=order_id, user=request.user)
        now = timezone.now()
        cancellation_datetime = datetime.combine(now.date(), order.food_category.cancellation_time)
        cancellation_datetime = timezone.make_aware(cancellation_datetime, timezone.get_current_timezone())
        print(f"{now=}")
        print(f"{cancellation_datetime=}")

        if now > cancellation_datetime:
            messages.error(request, "Late for order cancellation")
            return redirect('orders')
        
        latest_date = Orders.objects.filter(subscription_id=order.subscription_id, 
                                            food_category=order.food_category).aggregate(Max('delivery_date'))['delivery_date__max']
        
        if latest_date:
            next_date = latest_date + timedelta(days=1)
            order.delivery_date = next_date
            order.save()
            subscription = get_object_or_404(Subscriptions, order.subscription_id)
            subscription.end_date = next_date
            subscription.save()
            messages.success(request, f"Order rescheduled successfully to {next_date}.")
        else:
            messages.error(request, "Order cannot be rescheduled.")

    except Exception as e:
        print(f"{e=}")
        messages.error(request,"Server error")
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