# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CustomUser, UserProfile, Locations, RestaurantProfile
from users.models import Wallet
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import CustomUser
from django.urls import reverse




@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'normal':
        UserProfile.objects.create(user=instance)
        Wallet.objects.get_or_create(user=instance)    

@receiver(post_save, sender=RestaurantProfile)
def send_email_on_new_restaurant(sender, instance, created, **kwargs):
    if created:
        admin_emails = list(CustomUser.objects.filter(is_superuser=True).values_list('email', flat=True))
        url = reverse('restaurants')
        send_mail(
            subject='New Restaurant Registration',
            message=f'''
            A new restaurant has registered, Approve it now!:
            Name: {instance.restaurant_name}
            Owner: {instance.owner_name}
            Email: {instance.email}
            Phone: {instance.contact_number}
            Location: {instance.location_name}
            Approved: {instance.is_approved}
            View here: http://localhost:8000{url}
                    ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,  # Change this to the actual admin email(s)
            fail_silently=False,
        )