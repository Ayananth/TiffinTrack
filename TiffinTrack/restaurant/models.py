from django.db import models
from django.conf import settings
from accounts.models import RestaurantProfile





class MenuItem(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    food_category = models.CharField(max_length=50)
    price_category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
