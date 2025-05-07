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






def home(request):
    print(request.user)
    all_locations = Locations.objects.all()

    default_location = get_object_or_404(Locations, name="thrissur")
    user_profile = None
    current_location = default_location

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.filter(user=request.user).select_related('location').first()
        if user_profile and user_profile.location:
            current_location = user_profile.location

    restaurants = []

    if request.method == "POST":
        form_id = request.POST.get('form_id')
        print(f"Form ID: {form_id}")

        if form_id == 'location_form':
            print("Location form submitted")
            location_id = request.POST.get("selected_location")
            selected_location = Locations.objects.filter(id=location_id).first()

            if selected_location:
                current_location = selected_location
                if request.user.is_authenticated and user_profile:
                    user_profile.location = selected_location
                    user_profile.save()
                    messages.success(request, "Location updated.")
                elif request.user.is_authenticated:
                    messages.error(request, "User profile not found.")
            else:
                current_location = default_location
                messages.error(request, "Invalid location selected.")

        elif form_id == 'restaurant_form':
            print("Restaurant search")
            restaurant_name = request.POST.get('restaurant_name', '').strip()
            if restaurant_name:
                restaurants = RestaurantProfile.objects.filter(
                    is_approved=True,
                    location=current_location,
                    restaurant_name__icontains=restaurant_name
                ).annotate(avg_rating=Avg('reviews__rating'))
            else:
                restaurants = RestaurantProfile.objects.filter(
                    is_approved=True,
                    location=current_location
                ).annotate(avg_rating=Avg('reviews__rating'))

    # Default restaurant list if not loaded in POST
    if not restaurants:
        restaurants = RestaurantProfile.objects.filter(
            is_approved=True,
            location=current_location
        ).annotate(avg_rating=Avg('reviews__rating'))

    # Add min and max total_price
    for restaurant in restaurants:
        menu_categories = restaurant.menu_categories.filter(is_active=True)
        total_prices = [category.total_price for category in menu_categories]
        restaurant.min_total_price = int(min(total_prices)) if total_prices else 0
        restaurant.max_total_price = int(max(total_prices)) if total_prices else 0

    context = {
        'restaurants': restaurants,
        'location': current_location,
        'all_locations': all_locations,
        'restaurant_name': restaurant_name if request.method == "POST" and form_id == "restaurant_form" else ''
    }

    return render(request, './users/home.html', context)


@login_required(login_url='login')
def update_profile(request):
    user = request.user
    profile = user.userprofile
    location  = profile.location
    print("test")
    print(profile.address)

    user_form = UserUpdateForm(instance=user)
    print(f"{user.userprofile=}")
    profile_form = ProfileUpdateForm(instance=user.userprofile)

    if request.method == 'POST':
        print("POST request received")
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.userprofile)

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

def update_user_location(request):
    print(request.POST)
    print("update_user_location")
    




    return redirect('user-home')




def restaurant_details(request, pk):
    restaurant = get_object_or_404(RestaurantProfile, pk=pk)
    avg_rating = restaurant.reviews.aggregate(Avg('rating'))['rating__avg']
    reviews = restaurant.reviews.all().count()
    location = restaurant.location
    menu_categories = MenuCategory.objects.filter(is_active=True)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    menu_data = []

    for menu_category in menu_categories:
        category_prices = {}
        weekly_menu = defaultdict(lambda: {"Breakfast": [], "Lunch": [], "Dinner": []})

        # Get all food items for this menu category
        food_items = FoodItem.objects.filter(menu_category=menu_category, is_available=True)

        # Get prices for only those food categories that belong to this menu
        food_categories = FoodCategory.objects.filter(menu_categories=menu_category, is_active=True)
        for food_cat in food_categories:
            category_prices[food_cat.name] = food_cat.price
            print(f"Category: {food_cat.name}, Price: {food_cat.price}")

        for item in food_items:
            # Only include items with both a food_category and a day
            if item.food_category and item.day:
                weekly_menu[item.day][item.food_category.name].append(item.name)

        # Sort the weekly menu based on day order
        sorted_menu = {day: weekly_menu[day] for day in days_order}

        total_price = sum(category_prices.values())
        menu_data.append({
            'menu_category': menu_category.name,
            'weekly_menu': sorted_menu,
            'category_prices': category_prices,
            'total_price': total_price,
        })


    context = {
        'restaurant': restaurant,
        'rating': avg_rating,
        'reviews': reviews,
        'location': restaurant.location,
         'menu_data': menu_data,
        
    }

    print(context)
    return render(request, 'users/restaurant_detail.html', context)
    
    
    



@login_required
def subscribe(request, plan_id):
    plan = MenuCategory.objects.get(id=plan_id)
    
    
    Subscriptions.objects.update_or_create(
        user=request.user,
        defaults={
            'restaurant': plan.restaurant,
            'menu_category': plan,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timezone.timedelta(days=plan.duration_days),
            'is_active': True,
        }
    )
    return redirect('subscription_success')