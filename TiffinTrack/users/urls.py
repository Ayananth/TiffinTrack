from django.urls import path
from . import views

urlpatterns = [
    # path('login/',views.user_login, name='user-login'),
    # path('logout/',views.user_logout, name='user-logout'),
    # path('register/',views.register, name='user-register'),
    path('',views.home, name='user-home'),
    path('profile/',views.update_profile, name='user-profile'),
    path('restaurant/<int:pk>',views.restaurant_details, name='restaurant-details'),
    path('update-location', views.update_user_location, name='update-location')


]