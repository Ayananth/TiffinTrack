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
    



class FoodCategory(models.Model):
    name = models.CharField(max_length=50)  # e.g., Breakfast, Lunch, Dinner
    price = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='food_categories'
    )
    is_active = models.BooleanField(default=True)  # To mark if the category is active or not

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('restaurant', 'name')  # Prevent duplicate names within the same restaurant
        ordering = ['name']


class MenuCategory(models.Model):
    name = models.CharField(max_length=50)  # e.g., Basic, Premium
    food_categories = models.ManyToManyField(
        FoodCategory,
        related_name='menu_categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    restaurant = models.ForeignKey(RestaurantProfile,on_delete=models.CASCADE,related_name='menu_categories')
    is_active = models.BooleanField(default=True)  # To mark if the category is active or not
    def __str__(self):
        return self.name

    @property
    def total_price(self):
        return self.food_categories.aggregate(
            total=models.Sum('price')
        )['total'] or 0

    class Meta:
        unique_together = ('restaurant', 'name')
        ordering = ['name']


class FoodItem(models.Model):
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='food_items'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_vegetarian = models.BooleanField(default=False)

    menu_category = models.ForeignKey(
        MenuCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_items'
    )
    food_category = models.ForeignKey(
        FoodCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_items'
    )

    def __str__(self):
        food_cat = self.food_category.name if self.food_category else "No FoodCat"
        menu_cat = self.menu_category.name if self.menu_category else "No MenuCat"
        return f"{self.name} - {food_cat} - {menu_cat}"

    class Meta:
        ordering = ['-created_at']
