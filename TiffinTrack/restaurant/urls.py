from django.urls import path
from . import views
urlpatterns = [
    # path('login/',views.restaurant_login, name='restaurant-login'),
    path('logout/',views.restaurant_logout, name='restaurant-logout'),
    path('register/',views.restaurant_register, name='restaurant-register'),
    path('restaurant-profile/',views.profile, name='restaurant-profile'),
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
    

    path('food_items/', views.foods, name='restaurant-food_items'),
    path('food_items/add', views.food_add_or_update, name='restaurant-food_items-add'),
    path('food_items/edit/<int:pk>/', views.food_add_or_update, name='restaurant-food_items-edit'),
    path('food_items/delete/<int:id>/', views.delete_food_item, name='restaurant-food_items-delete'),

    path('users/', views.users, name='restaurant-users'),

    path('orders/', views.orders, name='restaurant-orders'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='restaurant-cancel_order'),
    path('orders/delivered/<int:order_id>/', views.deliver_order, name='restaurant-deliver-order'),










]