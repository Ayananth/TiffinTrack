
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/',views.accounts_login, name='login'),
    path('logout/',views.accounts_logout, name='logout'),
    path('signup/',views.accounts_sign_up, name='register'),
    path('signup/<int:id>/',views.accounts_sign_up, name='register'),
    path('', include('allauth.urls')),
    # path('send_otp/', views.send_otp, name='send_otp'),
    path('verify_otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('resend_otp/<int:user_id>/', views.resend_otp, name='resend_otp'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),


    path("request-email-change/", views.request_email_change, name="request_email_change"),
    path("confirm-email-change/", views.confirm_email_change, name="confirm_email_change"),

    path('change-password/', views.request_password_change, name='request_password_change'),
    path("confirm-password-change/<str:token>/", views.confirm_password_change, name="confirm_password_change"),



]