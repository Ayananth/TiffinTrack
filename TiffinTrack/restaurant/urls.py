from django.urls import path
from . import views

urlpatterns = [
    path('login/',views.restaurant_login, name='restaurant-login'),
    path('logout/',views.restaurant_logout, name='restaurant-logout'),
    path('register/',views.restaurant_register, name='restaurant-register'),
    path('home/',views.home, name='restaurant-home'),
]