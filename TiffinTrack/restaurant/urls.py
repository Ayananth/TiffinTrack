from django.urls import path
from . import views
from coupons import views as coupon_views
urlpatterns = [
    # path('login/',views.restaurant_login, name='restaurant-login'),
    path('logout/',views.restaurant_logout, name='restaurant-logout'),
    path('register/',views.restaurant_register, name='restaurant-register'),
    path('register/<str:editing>/',views.restaurant_register, name='restaurant-register'),

    path('restaurant-profile/',views.profile, name='restaurant-profile'),
    path('home/',views.home, name='restaurant-home'),




    path('food_items/', views.foods, name='restaurant-food_items'),
    path('food_items/add', views.food_add_or_update, name='restaurant-food_items-add'),
    path('food_items/edit/<int:pk>/', views.food_add_or_update, name='restaurant-food_items-edit'),
    path('food_items/delete/<int:id>/', views.delete_food_item, name='restaurant-food_items-delete'),

    path('users/', views.users, name='restaurant-users'),

    path('orders/', views.orders, name='restaurant-orders'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='restaurant-cancel_order'),
    path('orders/delivered/<int:order_id>/', views.deliver_order, name='restaurant-deliver-order'),

    path('menu_items/', views.menus, name='restaurant-menu_items'),
    path('menu_items/add', views.menu_add_or_update, name='restaurant-menu_items-add'),
    path('menu_items/edit/<int:pk>/', views.menu_add_or_update, name='restaurant-menu_items-edit'),
    path('menu_items/delete/<int:id>/', views.menu_food_item, name='restaurant-menu_items-delete'),


    path('food_category/', views.food_category, name='restaurant-food_category'),
    path('food_category/add', views.category_add_or_update, name='restaurant-food_category-add'),
    path('food_category/edit/<int:pk>/', views.category_add_or_update, name='restaurant-food_category-edit'),
    path('food_category/delete/<int:id>/', views.delete_food_category, name='restaurant-food_category-delete'),

    path('offers/', views.offers, name='restaurant-offers'),
    path('offers/add', views.offer_create_or_update, name='restaurant-offer-add'),
    path('offers/edit/<int:pk>/', views.offer_create_or_update, name='restaurant-offer-edit'),
    path('offers/delete/<int:pk>/', views.offer_delete, name='restaurant-offer-delete'),


    path('images/add/<int:pk>/', views.image_add, name='add-restaurant-image'),
    path('images/delete/<int:pk>/', views.image_delete, name='delete-restaurant-image'),


    path('coupons/', views.coupons, name='restaurant-coupons'),
    path('coupons/add', coupon_views.restaurant_coupon_form, name='restaurant-coupons-add'),
    path('coupons/add/<int:coupon_id>/', coupon_views.restaurant_coupon_form, name='restaurant-coupons-edit'),
    path('coupons/delete/<int:coupon_id>/', coupon_views.restaurant_delete_coupon, name='restaurant-coupons-delete'),


    path('payments/', views.payment_dashboard, name='payment'),
    path('payments/export/', views.export_payments_csv, name='export-payments-csv'),


    



    










]