
from django.urls import path, include
from . import views

urlpatterns = [
    path('login/',views.accounts_login, name='login'),
    path('logout/',views.accounts_logout, name='logout'),
    path('signup/',views.accounts_sign_up, name='register'),
    path('', include('allauth.urls')),
    path('send_otp/', views.send_otp, name='send_otp'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),


]