from django.contrib import admin
from restaurant.models import RestaurantProfile
from .models import Address, Orders

# Register your models here.

admin.site.register(Address)
admin.site.register(Orders)



