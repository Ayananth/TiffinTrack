# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CustomUser, UserProfile, Locations, RestaurantProfile
from users.models import Wallet
from django.conf import settings
from accounts.models import CustomUser
from django.urls import reverse
from .utils import send_templated_email
from coupons.models import Referral
from dotenv import load_dotenv
import os

load_dotenv()


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if (
        instance.user_type == "normal"
        and not instance.is_superuser
        and not instance.is_staff
    ):
        UserProfile.objects.get_or_create(user=instance)
        Wallet.objects.get_or_create(user=instance)
        Referral.objects.get_or_create(user=instance)
    else:
        # If a user is staff/superuser/non-normal, ensure no normal-user profile exists.
        UserProfile.objects.filter(user=instance).delete()


@receiver(post_save, sender=RestaurantProfile)
def send_email_on_new_restaurant(sender, instance, created, **kwargs):
    if created:
        admin_emails = list(
            CustomUser.objects.filter(is_superuser=True).values_list("email", flat=True)
        )
        url = reverse("restaurants")
        domain = os.environ.get("DOMAIN_URL", "https://ayananth.xyz/")
        send_templated_email(
            subject="TiffinTrack - New Restaurant Registration",
            recipient_list=admin_emails,
            heading="New Restaurant Registration Request",
            intro="A new restaurant has completed registration and is waiting for approval.",
            details={
                "Restaurant": instance.restaurant_name,
                "Owner": instance.owner_name,
                "Email": instance.email,
                "Phone": instance.contact_number,
                "Location": instance.location_name,
                "Approved": instance.is_approved,
            },
            action_text="Review Restaurant",
            action_url=f"{domain}{url}",
            preheader="Action needed: approve new restaurant profile.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            fail_silently=False,
        )
