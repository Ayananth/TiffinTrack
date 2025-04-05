from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from users.forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from .models import RestaurantProfile, MenuItem
from .forms import UserProfileForm




def restaurant_login(request):
    
    if request.user.is_authenticated:
        return redirect('restaurant-home')
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print("logging in")
            login(request, user)
            return redirect('restaurant-home')
        else:
            print("Invalid credentials")
            messages.success(request, "Invalid username or password")
    return render(request, './restaurant/login.html')


@login_required(login_url='restaurant-login')
def home(request):
    print("Home page")
    print(request.user)
    if not request.user.is_restaurant_user:
        print("not restaurant user")
        messages.success(request, "not restaurant user")

        return render(request, './restaurant/login.html')
    

    restaurant = RestaurantProfile.objects.filter(user=request.user).first()
    menu_items = {}
    print(f"{restaurant=}")
    if restaurant:
        if restaurant.is_approved:
            menu_items = MenuItem.objects.filter(restaurant=restaurant)
            print(f"{menu_items=}")

        
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            restaurant_profile = form.save(commit=False)  # Don't save yet
            restaurant_profile.user = request.user        # Assign the user
            restaurant_profile.save()                     # Now save it
            return render(request, './restaurant/home.html')

    else:
        form = UserProfileForm()

   

    return render(request, './restaurant/home.html', context={'form':form, 'restaurants': restaurant, 'menu_items':menu_items})

def restaurant_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('restaurant-login')


def restaurant_register(request):
    if request.user.is_authenticated:
        return redirect('restaurant-home')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)  
        if form.is_valid():
            user = form.save(commit=False)  # Don't save to database yet
            user.user_type = 'restaurant'   # Set user_type explicitly
            user.save()  # Now save to database
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username}! Try login")
            return redirect('restaurant-login')   
    else:
        form = UserRegisterForm()
    context = {  
        'form':form  
    }  
    return render(request, './restaurant/register.html', context)  


