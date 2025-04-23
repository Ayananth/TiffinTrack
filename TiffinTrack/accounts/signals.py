# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CustomUser, UserProfile, Locations


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'normal':
        try:
            default_location = Locations.objects.get(name='thrissur')
        except Locations.DoesNotExist:
            default_location = None  # or raise an error/log warning
        UserProfile.objects.create(user=instance, location=default_location)    

