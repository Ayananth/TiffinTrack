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



from .models import Address
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




    context = {
        'restaurants': restaurants,
        'location': location_name
    }

    return render(request, './users/home.html', context)


@login_required(login_url='login')
def update_profile(request):
    user = request.user
    profile = user.profile

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
            user_form.save()
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
def manage_user_address(request):
    user=request.user
    addresses = Address.objects.filter(user=user)
    context = {"addresses": addresses}

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
    