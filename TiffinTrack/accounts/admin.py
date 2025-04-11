from django.contrib import admin
from .models import CustomUser, Locations, UserProfile, RestaurantProfile

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(RestaurantProfile)
admin.site.register(Locations)
admin.site.register(UserProfile)


