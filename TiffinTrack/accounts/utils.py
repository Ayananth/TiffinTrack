from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect


def login_redirect_view(request):
    user = request.user
    print(user)
    if user.is_normal_user:
        return reverse('user-home')
    elif user.is_restaurant_user:
        return render('restaurant-home')
    elif user.is_admin:
        return reverse('admin-home')
    else:
        return reverse('user-home')