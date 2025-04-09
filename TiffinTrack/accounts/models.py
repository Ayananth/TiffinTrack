# from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random



# class CustomUser(AbstractUser):
#     USER_TYPE_CHOICES = (
#         ('normal', 'Normal User'),
#         ('restaurant', 'Restaurant User'),
#         ('admin', 'Admin'),
#     )
#     user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='normal')

#     def __str__(self):
#         return self.username
    
#     @property
#     def is_normal_user(self):
#         return self.user_type == 'normal'

#     @property
#     def is_restaurant_user(self):
#         return self.user_type == 'restaurant'

#     @property
#     def is_admin(self):
#         return self.user_type == 'admin'

class PhoneOTP(models.Model):
    phone = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.timestamp = timezone.now()
        self.save()