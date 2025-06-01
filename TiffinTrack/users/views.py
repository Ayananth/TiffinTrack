import re
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_GET

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from accounts.forms import UserUpdateForm, ProfileUpdateForm
from restaurant.forms import ReviewForm
from django.contrib.auth.decorators import login_required
from restaurant.models import RestaurantProfile, FoodItem, FoodCategory, MenuCategory, Subscriptions, Offer, Review
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
from coupons.models import Coupon, CouponUsage

from django.http import JsonResponse

from django.utils import timezone
from django.template.loader import render_to_string
from accounts.models import CustomUser

from .constants import *








from .models import Address, Orders, Wallet
from .forms import AddressForm, SubscriptionForm
from django.utils import timezone
from collections import defaultdict
from coupons.models import Referral




@login_required(login_url='login')
def home(request):
    print(request.user)
    user = request.user
    restaurant_name = request.GET.get('restaurant_name')
    print(user.profile.point)
    reference_point = user.profile.point


    referral = request.session.get('referral_code')
    print(referral)
    if referral:
        try:
            referral_obj = Referral.objects.get(code=referral)
            if referral_obj.user != user and not user.profile.referral_code_used and not referral_obj.referred_users.filter(id=user.id).exists():
                referral_obj.referred_users.add(user)
                referral_obj.save()
                user.profile.referral_code_used = referral
                user.profile.save()
        except Referral.DoesNotExist:
            pass
        del request.session['referral_code']



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

    # Collect restaurant IDs shown on this page
    restaurant_ids = [restaurant.id for restaurant in page_obj]

    # Get active offers for those restaurants
    now = timezone.now()
    active_offers = Offer.objects.filter(
        restaurant_id__in=restaurant_ids,
        is_active=True,
        valid_from__lte=now,
        valid_until__gte=now
    ).select_related('restaurant').prefetch_related('menu_categories')

    # Group offers by restaurant
    restaurant_offers = defaultdict(list)
    for offer in active_offers:
        restaurant_offers[offer.restaurant_id].append(offer)

    print(dict(restaurant_offers))




    context = {
        'restaurants': page_obj,
        'restaurant_offers': dict(restaurant_offers),
        'offer':True
    }

    return render(request, './users/home.html', context)


@login_required(login_url='login')
def update_profile(request):
    return render(request, 'users/profile.html')


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

    next = request.GET.get('next')

    # Restaurant summary
    avg_rating = restaurant.reviews.aggregate(Avg('rating'))['rating__avg']
    reviews_count = restaurant.reviews.count()
    reviews = Review.objects.filter(restaurant=restaurant)


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

    has_reviewed = False

    review = Review.objects.filter(user=request.user, restaurant=restaurant).first()
    if not review:
        review=None
    has_reviewed = review is not None
    review_form = ReviewForm(instance=review)


    context = {
        'restaurant': restaurant,
        'rating': avg_rating,
        'reviews': reviews_count,
        'menu_data': menu_data,
        'review_list': reviews,
        'review_form': review_form,
        'has_reviewed': has_reviewed,
        'next':next
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
            subscription.per_day_amount = menu.total_price
            subscription.total_amount = number_of_days.days * menu.total_price
            subscription.num_days = number_of_days.days+1
            subscription.address = form.cleaned_data.get('address')
            subscription.save()


            return redirect('payment', id=subscription.id)
        else:
            messages.error(request, "Form not valid")
            print("Form not valid")
    else:
        form = SubscriptionForm()
        
    address_form = AddressForm()


    context = {'addresses': addresses,  'form': form, 'address_form': address_form}
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
    subscription.is_active = True
    subscription.user = request.user
    start_date = subscription.start_date.date()
    end_date = subscription.end_date.date()
    menu = subscription.menu_category
    food_categories = menu.food_categories.all()
    print(f"{food_categories=}")
    orders_to_create = []
    current_date = start_date
    while current_date <= end_date:
        for food_category in food_categories:
            # Check if an order already exists
            order_exists = Orders.objects.filter(
                user=request.user,
                restaurant=subscription.restaurant,
                food_category=food_category,
                delivery_date=current_date,
                subscription_id=subscription
            ).exists()

            if not order_exists:
                orders_to_create.append(Orders(
                    user=request.user,
                    restaurant=subscription.restaurant,
                    food_category=food_category,
                    food_item=None,
                    delivery_date=current_date,
                    status='PENDING',
                    address=subscription.address,
                    subscription_id=subscription
                ))
        current_date += timedelta(days=1)

    if orders_to_create:
        Orders.objects.bulk_create(orders_to_create)
    subscription.save()

    wallet_amount = subscription.wallet_amount_used
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if wallet_amount:
        wallet.debit(int(wallet_amount), description=f"Used for subscription")

    del request.session['subscription']


    #add referal bonus
    profile = request.user.profile

    if profile.referral_code_used and not profile.referral_bonus_used:
        try:
            referred_by = Referral.objects.get(code = profile.referral_code_used)
            #add wallet amounts

            #current user wallet
            wallet.credit(REFERRAL_AMOUNT, description=f"Referral bonus")
            #referer wallet
            referer_wallet,_ = Wallet.objects.get_or_create(user=referred_by.user)
            referer_wallet.credit(REFERRER_AMOUNT, description=f"Referral bonus from {request.user}")
            profile.referral_bonus_used = True
            profile.save()
            referred_by.bonus_earned += REFERRER_AMOUNT
            referred_by.save()
            



        except Referral.DoesNotExist:
            pass


    return render(request, 'users/success.html')


@login_required(login_url='login')
def payment(request, id):
    wallet = request.user.wallet.balance
    subscription_id = id
    try:
        subscription = Subscriptions.objects.get(id=subscription_id)
    except Subscriptions.DoesNotExist:
        messages.error(request, "Please try again! ")
        return redirect('payment', id=subscription_id)
    
    if request.method == 'POST':
        request.session['subscription'] = subscription.id
        if subscription.final_total>0:
            return redirect('initiate_payment')
        else:
            return redirect('order-confirm')
        
    
    context = {'subscription': subscription,
               'wallet_amount': wallet}
    
    return render(request, 'users/payment.html', context)


@login_required(login_url='login')
@require_POST
def use_wallet(request):
    subscription_id = request.POST.get('subscription_id')
    print(f"{subscription_id=}")
    try:
        subscription = Subscriptions.objects.get(id=subscription_id)
        print(subscription)
    except Subscriptions.DoesNotExist:
        print("Item not found")
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
        subscription = Subscriptions.objects.get(id=subscription_id)
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

    subscription = Subscriptions.objects.filter(is_active=True, user=user).order_by('-created_at').first()
    print(f"{subscription=}")

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
        delivered = orders.filter(food_category=food_category, status='DELIVERED').count()
        cancelled = orders.filter(food_category=food_category, status='CANCELLED').count()
        pending = orders.filter(food_category=food_category, status='PENDING').count()

        data['delivered'] = delivered
        data['cancelled'] = cancelled
        data['pending'] = pending

        print(f"{refund=}")
        refund += delivered * food_category.price
        print(f"{refund} = {pending} * {food_category.price}")

        print(f"{refund=}")

        refund = subscription.final_total - refund
        

        delivery_data[food_category] = data  # or food_category.name if it has one
        
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
    subscription = user.subscriptions.filter(is_active=True).order_by('-created_at').first()
    print(f"{subscription=}")

    sort_by = request.GET.get('sort', 'delivery_date')  # default: delivery_date
    direction = request.GET.get('dir', 'asc') 
    order_prefix = '' if direction == 'asc' else '-'
    valid_sort_fields = ['delivery_date', 'status']
    sort_field = sort_by if sort_by in valid_sort_fields else 'delivery_date'

    status = request.GET.get('status')
    delivery_date = request.GET.get('delivery_date')

    orders = Orders.objects.filter(user=user, status="PENDING").order_by(f"{order_prefix}{sort_field}")

    if subscription:
        orders = orders.filter(subscription_id=subscription)

    if status:
        orders = orders.filter(status=status)

    if delivery_date:
        orders = orders.filter(delivery_date=delivery_date)


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
                }
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
        cancellation_datetime = datetime.combine(order.delivery_date, order.food_category.cancellation_time)
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
            subscription = order.subscription_id
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


@login_required(login_url='login')
def add_user_address(request):
    user = request.user
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            return JsonResponse({'success': True, 'message': 'Address added successfully'})
        else:
            form_html = render_to_string('users/address_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        return JsonResponse({'error': 'Only POST allowed'}, status=400)
    




def post_review(request):
    restaurant_id = request.POST.get('restaurant_id')
    if not restaurant_id:
        return redirect('user-home')

    restaurant = get_object_or_404(RestaurantProfile, id=restaurant_id)

    restaurant_id = restaurant.id
    redirect_url = reverse('restaurant-details', kwargs={'pk': restaurant_id})
    query_string = urlencode({'next': 'review'})
    

    # Get existing review if any
    existing_review = Review.objects.filter(restaurant=restaurant, user=request.user).first()

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)  # pre-fill if exists
        if form.is_valid():
            review = form.save(commit=False)
            review.restaurant = restaurant
            review.user = request.user
            review.save()

            if existing_review:
                messages.success(request, "Your review has been updated successfully.")
            else:
                messages.success(request, "Your review has been submitted successfully.")

            # return redirect('restaurant-details', pk=restaurant.id)
            return redirect(f'{redirect_url}?{query_string}')
        else:
            messages.error(request, "Please correct the errors in the form.")

    return redirect(f'{redirect_url}?{query_string}')

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    # Ensure that only the author can delete their review
    if review.user != request.user:
        messages.error(request, "You are not allowed to delete this review.")
        return redirect('restaurant-detail', id=review.restaurant.id)

    restaurant_id = review.restaurant.id
    redirect_url = reverse('restaurant-details', kwargs={'pk': restaurant_id})
    query_string = urlencode({'next': 'review'})
    review.delete()
    messages.success(request, "Your review has been deleted.")
    return redirect(f'{redirect_url}?{query_string}')


@login_required(login_url='login')
def update_profile_pic(request):
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        profile = request.user.profile
        profile.profile_pic = request.FILES['profile_pic']
        profile.save()
        messages.success(request, "Profile picture updated successfully.")
        return redirect('user-profile')  # Replace with your actual profile view name
    else:
        messages.error(request, "Please upload a valid image.")
    
    return render(request, 'users/update_profile_pic.html')

@login_required
def change_username(request):
    if request.method == "POST":
        new_username = request.POST.get("username", "").strip()
        if not new_username:
            messages.error(request, "Username cannot be empty.")
            return redirect("user-profile")
        if new_username == request.user.username:
            messages.error(request, "New username must be different from the current one.")
            return redirect("user-profile")
        if CustomUser.objects.filter(username__iexact=new_username).exclude(id=request.user.id).exists():
            messages.error(request, "This username is already taken.")
            return redirect("user-profile")
        request.user.username = new_username
        request.user.save()
        messages.success(request, "Username successfully updated.")

    return redirect("user-profile")

@login_required
def update_phone_number(request):
    PHONE_REGEX = r'^\+?\d{10,15}$'
    user = request.user
    if request.method == "POST":
        new_phone = request.POST.get("phone", "").strip()
        
        if not new_phone:
            messages.error(request, "Phone number cannot be empty.")
            return redirect("user-profile")
        
        if not re.match(PHONE_REGEX, new_phone):
            messages.error(request, "Enter a valid phone number (10-15 digits, optional '+').")
            return redirect("user-profile")
               
        if user.phone == new_phone:
            messages.error(request, "New phone number must be different from the current one.")
            return redirect("user-profile")
        
        if CustomUser.objects.filter(phone=new_phone).exclude(id=request.user.id).exists():
            messages.error(request, "This phone number is already in use.")
            return redirect("user-profile")
        
        user.phone = new_phone
        user.save()
        messages.success(request, "Phone number updated successfully.")
    
    return redirect("user-profile")



@login_required
def refer(request):
    user = request.user
    referral, created = Referral.objects.get_or_create(user=user)
    pending = UserProfile.objects.filter(referral_code_used=referral.code, referral_bonus_used=False).count()


    context = {
        'title': 'Refer and Earn',
        'referral': referral,
        'pending': pending
    }



    return render(request,'./users/refer.html', context)


def get_available_coupons_for_user(user, restaurant=None):
    now = timezone.now()
    coupons = Coupon.objects.filter(active=True, valid_from__lte=now, valid_to__gte=now)

    if restaurant:
        coupons = coupons.filter(restaurant=restaurant)

    available_coupons = []

    for coupon in coupons:
        usage_count = CouponUsage.objects.filter(user=user, coupon=coupon).count()
        if usage_count < coupon.usage_limit:
            available_coupons.append(coupon)

    return available_coupons




@login_required
@require_GET
def available_coupons_json(request, restaurant_id=None):
    user = request.user
    restaurant = None

    if restaurant_id:
        try:
            restaurant = RestaurantProfile.objects.get(id=restaurant_id)
        except RestaurantProfile.DoesNotExist:
            return JsonResponse({"error": "Restaurant not found"}, status=404)

    coupons = get_available_coupons_for_user(user, restaurant)

    data = []
    for c in coupons:
        data.append({
            "code": c.code,
            "cashback_amount": float(c.cashback_amount),
            "min_order_value": float(c.min_order_value),
            "valid_from": c.valid_from.isoformat(),
            "valid_to": c.valid_to.isoformat(),
            "usage_limit": c.usage_limit,

        })

    print(f"{data=}")

    return JsonResponse({"coupons": data})
