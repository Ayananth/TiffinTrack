from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from users.forms import UserRegisterForm
from django.contrib.auth.decorators import login_required




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
            messages.error(request, "Invalid username or password")
    return render(request, './restaurant/login.html')


@login_required(login_url='restaurant-login')
def home(request):
    if not request.user.is_restaurant_user:
        #TODO set error message
        return render(request, './restaurant/login.html')
    return render(request, './restaurant/home.html')

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
