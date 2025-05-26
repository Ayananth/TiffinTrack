from django.contrib import admin
from .models import FoodCategory, MenuCategory, FoodItem, Review, Subscriptions, Offer

# Register your models here.
admin.site.register(FoodCategory)
admin.site.register(MenuCategory)
admin.site.register(FoodItem)
admin.site.register(Review)
admin.site.register(Subscriptions)
admin.site.register(Offer)

