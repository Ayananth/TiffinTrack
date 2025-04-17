from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='admin-home'),
    path('all-users/', views.all_users, name='all-users'),
    path('add-user/', views.add_users, name='add-user'),
    path('update-user/<int:id>/', views.update_user, name='update-user'),




    path('admin-login', views.admin_login, name='admin-login'),
    path('logout', views.admin_logout, name='admin-logout'),
    # path('delete/<int:id>/', views.delete, name='delete-user'),
    # path('update/<int:id>/', views.update, name='update-user'),
    # path('register/', views.register, name='register'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('restaurant_request/', views.restaurant_requests, name='restaurant_request'),
    path('restaurant_approve/<int:pk>/', views.restaurant_approve, name='restaurant_approve'),
    path('delete_restaurant/<int:id>/', views.delete_restaurant, name='delete-restaurant'),


]

