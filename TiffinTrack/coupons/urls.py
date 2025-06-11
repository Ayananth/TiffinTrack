from django.urls import path
from . import views

urlpatterns = [
    path('apply/',views.apply_coupon, name='apply-coupon'),
    path('remove/',views.remove_coupon, name='remove-coupon')
]