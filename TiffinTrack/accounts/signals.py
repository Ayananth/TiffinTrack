# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CustomUser, UserProfile, Locations
from users.models import Wallet


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'normal':
        UserProfile.objects.create(user=instance)
        Wallet.objects.get_or_create(user=instance)    

