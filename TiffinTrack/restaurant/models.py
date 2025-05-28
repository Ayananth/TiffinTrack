from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import RestaurantProfile
import datetime
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from coupons.models import Coupon
from decimal import Decimal
from decimal import Decimal, ROUND_DOWN








class MenuCategory(models.Model):
    name = models.CharField(max_length=50)  # e.g., Basic, Premium
    description = models.TextField(blank=True)
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


class FoodCategory(models.Model):
    name = models.CharField(max_length=50)  # e.g., Breakfast, Lunch, Dinner
    price = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    cancellation_time = models.TimeField()
    menu_category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='food_categories', null=True, blank=True)

    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='food_categories'
    )
    is_active = models.BooleanField(default=True)  # To mark if the category is active or not

    def __str__(self):
        return f"{self.name}-{self.restaurant}"

    class Meta:
        unique_together = ('restaurant', 'name')  # Prevent duplicate names within the same restaurant
        ordering = ['name']


class FoodItem(models.Model):

    DAY_CHOICES = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]



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

    day = models.CharField(max_length=10, choices=DAY_CHOICES, null=True, blank=True)

    def __str__(self):
        food_cat = self.food_category.name if self.food_category else "No FoodCat"
        menu_cat = self.menu_category.name if self.menu_category else "No MenuCat"
        return f"{self.name} - {food_cat} - {menu_cat}"

    class Meta:
        ordering = ['-created_at']



class Review(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # e.g., 1 to 5
    comment = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} rated {self.restaurant.restaurant_name} {self.rating}/5'
    


class Subscriptions(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions', null=True, blank=True)
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name='subscriptions')
    menu_category = models.ForeignKey(MenuCategory,on_delete=models.SET_NULL,null=True,blank=True,related_name='subscriptions')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    extended_end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    address = models.ForeignKey('users.Address', on_delete=models.SET_NULL, null=True, blank=True, related_name='subscriptions')
    num_days = models.IntegerField(blank=True, null=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    wallet_amount_used = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def offer_discount(self):
        if not self.menu_category:
            return Decimal('0.00')

        now = timezone.now()
        active_offers = Offer.objects.filter(
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now,
            restaurant=self.restaurant,
            menu_categories=self.menu_category
        ).order_by('-discount_percent')  # Take highest if multiple

        if active_offers.exists():
            offer = active_offers.first()
            offer_amount = (self.menu_category.total_price * self.num_days) * (offer.discount_percent / 100)
            return Decimal(offer_amount).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        return Decimal('0.00')

    @property
    def item_total(self):
        amount = self.menu_category.total_price * self.num_days
        return Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    @property
    def discount(self):
        if self.coupon:
            return Decimal(self.coupon.cashback_amount).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        return Decimal('0.00')

    @property
    def total_after_discount(self):
        base_total = self.item_total
        offer_amount = self.offer_discount
        coupon_discount = self.discount

        total = base_total - offer_amount - coupon_discount
        return total.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

    @property
    def final_total(self):
        total = self.total_after_discount - self.wallet_amount_used
        return max(total, Decimal('0.00')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)



    def clean(self):
        super().clean()
        if self.user_id and self.is_active:
            existing_active = Subscriptions.objects.filter(user=self.user, is_active=True)
            if self.pk:
                existing_active = existing_active.exclude(pk=self.pk)
            if existing_active.exists():
                raise ValidationError({
                    'is_active': _("User already has an active subscription.")
                })
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.extended_end_date = self.end_date
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user}'



# class Orders(models.Model):
    #need cancelled food items details by a user
    #if not cancelled, then the delivered food items should be also there
    



class Offer(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name='offers')
    name = models.CharField(max_length=100)  # e.g., "10% off on Premium Lunch"
    description = models.TextField(blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 10.00 for 10%
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    # Linking offers to categories
    menu_categories = models.ManyToManyField(MenuCategory, blank=True, related_name='offers')
    food_categories = models.ManyToManyField(FoodCategory, blank=True, related_name='offers')

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.restaurant.restaurant_name}"

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until
