
from django.urls import path, include
from . import views

urlpatterns = [
    path('login/',views.accounts_login, name='login'),
    path('signup/',views.accounts_sign_up, name='signup-user'),
    path('', include('allauth.urls')),

]