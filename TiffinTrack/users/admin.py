from django.contrib import admin
from .models import CustomUser
from restaurant.models import RestaurantProfile

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(RestaurantProfile)


