from django.urls import path
from . import views
from coupons import views as coupon_views

urlpatterns = [
    path('', views.home, name='admin-home'),
    path('all-users/', views.all_users, name='all-users'),
    path('add-user/', views.add_users, name='add-user'),
    path('update-user/<int:id>/', views.update_user, name='update-user'),
    path('delete-user/<int:id>', views.delete_user, name='delete-user'),



    path('admin-login', views.admin_login, name='admin-login'),
    path('logout', views.admin_logout, name='admin-logout'),
    # path('delete/<int:id>/', views.delete, name='delete-user'),
    # path('update/<int:id>/', views.update, name='update-user'),
    # path('register/', views.register, name='register'),
    path('restaurants/', views.restaurants, name='restaurants'),
    path('restaurants/add', views.restaurant_add_or_update, name='restaurant-add'),
    path('restaurants/edit/<int:pk>/', views.restaurant_add_or_update, name='restaurant-edit'),
    path('restaurant_request/', views.restaurant_requests, name='restaurant_request'),
    path('restaurant_approve/<int:pk>/', views.restaurant_approve, name='restaurant_approve'),
    path('restaurant/delete/<int:id>/', views.delete_restaurant, name='restaurant-delete'),
    path('restaurants/dashboard/<int:pk>', views.restaurant_dashboard, name='restaurant-dashboard'),



    path('food_items/', views.foods, name='food_items'),
    # path('food_items/add', views.food_add_or_update, name='food_items-add'),
    # path('food_items/edit/<int:pk>/', views.food_add_or_update, name='food_items-edit'),
    # path('food_items/delete/<int:id>/', views.delete_food_item, name='food_items-delete'),


    path('menu_items/', views.menus, name='menu_items'),
    path('menu_items/add', views.menu_add_or_update, name='menu_items-add'),
    path('menu_items/edit/<int:pk>/', views.menu_add_or_update, name='menu_items-edit'),
    path('menu_items/delete/<int:id>/', views.menu_food_item, name='menu_items-delete'),
    

    path('food_category/', views.food_category, name='food_category'),
    path('food_category/add', views.category_add_or_update, name='food_category-add'),
    path('food_category/edit/<int:pk>/', views.category_add_or_update, name='food_category-edit'),
    path('food_category/delete/<int:id>/', views.delete_food_category, name='food_category-delete'),

    path('orders/', views.orders, name='admin-orders'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='admin-cancel_order'),
    path('orders/delivered/<int:order_id>/', views.deliver_order, name='admin-deliver-order'),

    path('coupons/', views.coupons, name='admin-coupons'),
    path('coupons/add', coupon_views.coupon_form, name='admin-coupons-add'),
    path('coupons/add/<int:coupon_id>/', coupon_views.coupon_form, name='admin-coupons-edit'),
    path('coupons/delete/<int:coupon_id>/', coupon_views.delete_coupon, name='admin-coupons-delete'),



    




]

