from django.urls import path
from . import views

urlpatterns = [
    # path('login/',views.user_login, name='user-login'),
    # path('logout/',views.user_logout, name='user-logout'),
    # path('register/',views.register, name='user-register'),
    path('',views.home, name='user-home'),
    path('profile/',views.update_profile, name='user-profile'),
    path('restaurant/<int:pk>',views.restaurant_details, name='restaurant-details'),
    path('update-location', views.update_user_location, name='update-location'),
    path('subscribe/<int:id>', views.subscription_cart, name='subscription-request' ),
    path('order-confirm/', views.order_confirm, name='order-confirm' ),
    path('payment/<int:id>' ,views.payment, name='payment'),
    path('address/', views.manage_user_address, name='address'),
    path('address/edit/<int:id>', views.manage_user_address, name='address-edit'),
    path('orders/', views.orders, name='orders'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),


    path('wallet/', views.wallet, name='wallet'),







]