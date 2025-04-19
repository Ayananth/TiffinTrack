from django.contrib import admin
from .models import FoodCategory, MenuCategory, MenuItem, FoodItem

# Register your models here.
admin.site.register(FoodCategory)
admin.site.register(MenuCategory)
admin.site.register(FoodItem)
