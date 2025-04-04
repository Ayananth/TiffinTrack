from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='admin-home'),
    path('admin-login', views.admin_login, name='admin-login'),
    path('logout', views.admin_logout, name='admin-logout'),
    path('delete/<int:id>/', views.delete, name='delete-user'),
    path('update/<int:id>/', views.update, name='update-user'),
    path('register/', views.register, name='register'),
    path('restaurants/', views.restaurants, name='restaurants'),

]

