from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from accounts.forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from .models import RestaurantProfile, MenuItem, MenuCategory, FoodCategory
from .forms import RestaurantProfileForm, MenuCategoryForm





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
    if not request.user.is_restaurant_user:
        print("not restaurant user")
        messages.error(request, "not restaurant user")

        return render(request, './restaurant/login.html')
    

    restaurant = RestaurantProfile.objects.filter(user=request.user).first()
    menu_items = {}
    print(f"{restaurant=}")
    if restaurant:
        if restaurant.is_approved:
            menu_items = MenuItem.objects.filter(restaurant=restaurant)
            print(f"{menu_items=}")

        
    if request.method == 'POST':
        form = RestaurantProfileForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant_profile = form.save(commit=False)  # Don't save yet
            restaurant_profile.user = request.user        # Assign the user
            restaurant_profile.save()                     # Now save it
            return redirect('restaurant-home')
        else:
            print("Form not valid")
            print(form.errors)
            messages.error(request, "Form not valid")

    else:
        form = RestaurantProfileForm()


    return render(request, './restaurant/dashboard.html', context={'form':form, 'restaurants': restaurant, 'menu_items':menu_items})
    # return render(request, './restaurant/home.html', context={'form':form, 'restaurants': restaurant, 'menu_items':menu_items})


def restaurant_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('login')


@login_required(login_url='login')
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
            return redirect('login')   
    else:
        form = UserRegisterForm()
    context = {  
        'form':form  
    }  
    return render(request, './restaurant/register.html', context)  




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