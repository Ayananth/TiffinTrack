from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random
from django.conf import settings
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.geos import Point






class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('normal', 'Normal User'),
        ('restaurant', 'Restaurant User'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='normal')
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True, unique=True)


    def __str__(self):
        return self.username
    
    @property
    def is_normal_user(self):
        return self.user_type == 'normal'

    @property
    def is_restaurant_user(self):
        return self.user_type == 'restaurant'

    @property
    def is_admin(self):
        return self.user_type == 'admin'

class PhoneOTP(models.Model):
    phone = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.timestamp = timezone.now()
        self.save()



class Locations(models.Model):
    name = models.CharField(unique=True, default="thrissur")

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    location = models.ForeignKey(Locations, on_delete=models.SET_DEFAULT, default=None)
    point = geomodels.PointField(geography=True, default=Point(76.1626624, 10.436608))
    address = models.TextField(null=True, blank=True)
    # phone = models.CharField(max_length=15, null=True, blank=True, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_pic = models.ImageField(upload_to='uploads/', default='uploads/default.png')


    def __str__(self):
        return self.user.username

class RestaurantProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    restaurant_name = models.CharField(max_length=100)
    owner_name = models.CharField(max_length=100)
    licence_no = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    restaurant_image = models.ImageField(upload_to='uploads/', null=True)
    location = models.ForeignKey(Locations, on_delete=models.SET_DEFAULT, default=None)
    profile_pic = models.ImageField(upload_to='uploads/', default='uploads/default-restaurant.png')



    def __str__(self):
        return self.restaurant_name



