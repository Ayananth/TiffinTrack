from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
# from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from restaurant.models import RestaurantProfile
from accounts.models import UserProfile, Locations




# def user_login(request):
#     if request.user.is_authenticated:
#         return redirect('user-home')
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             print("logging in")
#             login(request, user)
#             return redirect('user-home')
#         else:
#             print("Invalid credentials")
#             messages.success(request, "Invalid username or password")
#     return render(request, './users/login.html')

# def user_logout(request):
#     logout(request)
#     request.session.flush() 
#     return redirect('user-login')



# def register(request):
#     if request.user.is_authenticated:
#         return redirect('user-home')
#     if request.method == 'POST':
#         form = UserRegisterForm(request.POST)  
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get('username')
#             messages.success(request, f"Account created for {username}! Try login")
#             return redirect('user-login')   
#     else:
#         form = UserRegisterForm()
#     context = {  
#         'form':form  
#     }  
#     return render(request, './users/register.html', context)  


@login_required(login_url='login')
def home(request):
    print(request.user)
    all_locations = Locations.objects.all()

    selected_location = "thrissur"


    if request.method == "POST":
        form_id = request.POST.get('form_id')
        print(f"Form ID: {form_id}")
        if form_id == 'location_form':
            print("Location form submitted")
            location_id = request.POST.get("selected_location")
            # Fetch the selected location
            selected_location = Locations.objects.filter(id=location_id).first()
            if selected_location:
                # Update user's location in the UserProfile
                user_profile = UserProfile.objects.filter(user=request.user).first()
                if user_profile:
                    user_profile.location = selected_location
                    user_profile.save()
                else:
                    messages.error(request, "User profile not found.")
            else:
                selected_location = "thrissur"
                messages.error(request, "Invalid location selected.")


    # Fetch user location (as a Locations instance, not just ID)
    user_profile = UserProfile.objects.filter(user=request.user).select_related('location').first()
    location = user_profile.location if user_profile and user_profile.location else selected_location
    # Filter restaurants
    restaurants = RestaurantProfile.objects.filter(is_approved=True, location=location)


    context = {'restaurants': restaurants, 'location': location, 'all_locations': all_locations}
    return render(request, './users/home.html', context)