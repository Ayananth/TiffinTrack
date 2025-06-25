from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import random
from django.conf import settings
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.geos import Point
from accounts.utils import get_location_from_point
from cloudinary_storage.storage import MediaCloudinaryStorage








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
    pending_email = models.EmailField(null=True, blank=True)
    email_change_token = models.CharField(max_length=64, null=True, blank=True)
    email_change_expiry = models.DateTimeField(null=True, blank=True)


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
    # user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(unique=True, default="thrissur")
    point = geomodels.PointField(geography=True, default=Point(76.1626624, 10.436608))

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='profile')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_pic = models.ImageField(storage=MediaCloudinaryStorage(),
                                    upload_to='tiffintrack/prod/profile_pics/',
                                    null=True)
    location_name = models.CharField(max_length=255, default="thrissur")
    point = geomodels.PointField(geography=True, default=Point(76.1626624, 10.436608))
    referral_code_used = models.CharField(max_length=10, blank=True, null=True)
    referral_bonus_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk:
            old = UserProfile.objects.get(pk=self.pk)
            if old.point != self.point:
                self.location_name = get_location_from_point(self.point.x, self.point.y)
        else:
            self.location_name = get_location_from_point(self.point.x, self.point.y)
        super().save(*args, **kwargs)




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
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    restaurant_image = models.ImageField(storage=MediaCloudinaryStorage(),
                                    upload_to='tiffintrack/prod/restaurant_pics/',
                                    null=True)
    point = geomodels.PointField(geography=True, default=Point(76.1626624, 10.436608))
    address = models.TextField(max_length=255, blank=True, null=True)
    location_name = models.TextField(blank=True, null=True, max_length=255)
    admin_comments = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old = RestaurantProfile.objects.get(pk=self.pk)
            if old.point != self.point:
                self.location_name = get_location_from_point(self.point.x, self.point.y)
        else:
            self.location_name = get_location_from_point(self.point.x, self.point.y)
        super().save(*args, **kwargs)

        
    def __str__(self):
        return self.restaurant_name



class RestaurantImage(models.Model):
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(storage=MediaCloudinaryStorage(),
                                    upload_to='tiffintrack/prod/restaurant_pics/',
                                    null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.restaurant.restaurant_name}"