from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
from .models import CustomUser


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        email = (user.email or "").strip().lower()
        email_prefix = email.split("@")[0] if "@" in email else email
        given_name = (data.get("given_name") or "").strip().lower()
        full_name = (data.get("name") or "").strip().lower()

        # Build a safe base username from email prefix.
        preferred_source = given_name or full_name or email_prefix
        base_username = slugify(preferred_source.replace(".", "-")) or "user"
        candidate = base_username
        counter = 1

        # Ensure username uniqueness for social signups.
        while CustomUser.objects.filter(username=candidate).exists():
            candidate = f"{base_username}{counter}"
            counter += 1

        user.username = candidate
        return user
