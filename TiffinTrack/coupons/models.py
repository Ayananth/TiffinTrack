from django.db import models
from django.conf import settings
from django.utils import timezone
from restaurant.models import
import random
import string

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    cashback_amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=1)  # per user
    restaurant = models.ManyToManyField(RestaurantProfile, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to
    
    def __str__(self):
        return f"{self.code}"

class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    subscription = models.ForeignKey('restaurant.Subscriptions', on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)


def generate_unique_referral_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Referral.objects.filter(code=code).exists():
            return code

class Referral(models.Model):
    code = models.CharField(max_length=10, unique=True, default=generate_unique_referral_code)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    referred_users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='referred_by', blank=True)
    bonus_earned = models.DecimalField(max_digits=6, decimal_places=2, default=0)