# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CustomUser, UserProfile, Locations, RestaurantProfile
from users.models import Wallet
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import CustomUser
from django.urls import reverse
from coupons.models import Referral
from dotenv import load_dotenv
import os
load_dotenv()




@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'normal':
        UserProfile.objects.create(user=instance)
        Wallet.objects.get_or_create(user=instance)    
        Referral.objects.get_or_create(user=instance)

@receiver(post_save, sender=RestaurantProfile)
def send_email_on_new_restaurant(sender, instance, created, **kwargs):
    if created:
        admin_emails = list(CustomUser.objects.filter(is_superuser=True).values_list('email', flat=True))
        url = reverse('restaurants')
        domain = os.environ.get("DOMAIN_URL", "https://ayananth.xyz/")
        send_mail(
            subject='TiffinTrack-New Restaurant Registration',
            message=f'''
            A new restaurant has registered, Approve it now!:
            Name: {instance.restaurant_name}
            Owner: {instance.owner_name}
            Email: {instance.email}
            Phone: {instance.contact_number}
            Location: {instance.location_name}
            Approved: {instance.is_approved}
            View here: {domain}{url}
                    ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )