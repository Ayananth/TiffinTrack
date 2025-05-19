from django.urls import path
from . import views
urlpatterns = [
    # path('login/',views.restaurant_login, name='restaurant-login'),
    path('logout/',views.restaurant_logout, name='restaurant-logout'),
    path('register/',views.restaurant_register, name='restaurant-register'),
    path('home/',views.home, name='restaurant-home'),


    # Menu Category URLs
    path('menu-categories/', views.menu_category_list, name='menu_category_list'),
    path('menu-categories/add/', views.menu_category_add, name='menu_category_add'),
    path('menu-categories/<int:pk>/edit/', views.menu_category_edit, name='menu_category_edit'),
    path('menu-categories/<int:pk>/delete/', views.menu_category_delete, name='menu_category_delete'),
    
    # # Food Category URLs
    path('food-categories/', views.food_category_list, name='food_category_list'),
    # path('food-categories/add/', views.food_category_add, name='food_category_add'),
    # path('food-categories/<int:pk>/edit/', views.food_category_edit, name='food_category_edit'),
    # path('food-categories/<int:pk>/delete/', views.food_category_delete, name='food_category_delete'),
    
    # # Food Item URLs
    # path('food-items/', views.food_item_list, name='food_item_list'),
    # path('food-items/add/', views.food_item_add, name='food_item_add'),
    # path('food-items/<int:pk>/edit/', views.food_item_edit, name='food_item_edit'),
    # path('food-items/<int:pk>/delete/', views.food_item_delete, name='food_item_delete'),

    path('users/', views.users, name='restaurant-users'),




]