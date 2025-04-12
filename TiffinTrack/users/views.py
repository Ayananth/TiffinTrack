from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
# from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required
from restaurant.models import RestaurantProfile




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
    restaurants = RestaurantProfile.objects.filter(is_approved=True)
    context = {'restaurants': restaurants}
    return render(request, './users/home.html', context)