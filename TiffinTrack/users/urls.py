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
    path('manage_subscription/', views.manage_subscription, name='manage_subscription'),
    path('orders/', views.orders, name='orders'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('orders/extend/<int:order_id>/', views.extend_subscription, name='extend_order'),
    path('wallet/', views.wallet, name='wallet'),
    path('use_wallet/', views.use_wallet, name='use_wallet'),
    path('remove_wallet/', views.remove_wallet, name='remove_wallet'),
    path('user/address/add/', views.add_user_address, name='add_user_address'),
    path('add_review/', views.post_review, name='add_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('update-profile-pic/', views.update_profile_pic, name='update-profile-pic'),
    path('update-user-name/', views.change_username, name='change-user-name'),
    path('update-phone/', views.update_phone_number, name='update-phone'),

    path('refer/', views.refer, name='refer'),

    path("api/coupons/", views.available_coupons_json, name="all_coupons"),
    path("api/coupons/<int:restaurant_id>/", views.available_coupons_json, name="restaurant_coupons"),


    path('invoice/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='invoice_pdf'),

    path('report/restaurant/<int:restaurant_id>/', views.report_restaurant, name='report-restaurant'),




]