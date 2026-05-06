from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
from .models import CustomUser


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    SOCIAL_SIGNUP_USER_TYPE_SESSION_KEY = "social_signup_user_type"

    def _get_signup_user_type(self, request):
        user_type = (request.session.get(self.SOCIAL_SIGNUP_USER_TYPE_SESSION_KEY) or "").strip().lower()
        if user_type in {"normal", "restaurant"}:
            return user_type
        return "normal"

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        requested_user_type = self._get_signup_user_type(request)
        user.user_type = requested_user_type

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

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)

        requested_user_type = self._get_signup_user_type(request)
        if not sociallogin.is_existing and user.user_type != requested_user_type:
            user.user_type = requested_user_type
            user.save(update_fields=["user_type"])

        request.session.pop(self.SOCIAL_SIGNUP_USER_TYPE_SESSION_KEY, None)
        return user

    def pre_social_login(self, request, sociallogin):
        super().pre_social_login(request, sociallogin)
        requested_user_type = self._get_signup_user_type(request)
        if requested_user_type != "restaurant":
            return

        email = (getattr(sociallogin.user, "email", "") or "").strip().lower()
        if not email:
            return

        existing_user = CustomUser.objects.filter(email__iexact=email).first()
        if existing_user and existing_user.user_type == "normal":
            existing_user.user_type = "restaurant"
            existing_user.save(update_fields=["user_type"])
