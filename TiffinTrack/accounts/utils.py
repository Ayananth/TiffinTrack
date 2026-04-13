from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
# utils/twilio_sms.py
from twilio.rest import Client
from django.conf import settings
from geopy.geocoders import Nominatim
import logging
logger = logging.getLogger('myapp') 



def login_redirect_view(request):
    from accounts.models import RestaurantProfile
    user = request.user
    if user.is_normal_user:
        return reverse('user-home')
    elif user.is_restaurant_user:
        restaurant_profile = RestaurantProfile.objects.filter(user=user).first()
        if not restaurant_profile or not restaurant_profile.is_active:
            return reverse('restaurant-register')
        return reverse('restaurant-home')
    elif user.is_admin:
        return reverse('admin-home')
    else:
        return reverse('user-home')
    



def send_otp_via_sms(phone_number, otp):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f'Your OTP is: {otp}',
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone_number
    )




account_sid = 'ACfe79894ddb3ea5206d1ecd14c78c1626'
auth_token = '23b84f54c786b8d49c37b1c3c40d2b11'
client = Client(account_sid, auth_token)


def send_otp_sms():
    try:
        verification = client.verify \
            .v2 \
            .services('VAdf09a320224ebf348a443a54f1cab8ce') \
            .verifications \
            .create(to='+919544670122', channel='sms')
        return "success"
    except Exception as e:
        return "failed"


def verify_otp_sms(otp):
    try:
        verification_check = client.verify \
            .v2 \
            .services('VAdf09a320224ebf348a443a54f1cab8ce') \
            .verification_checks \
            .create(to='+919544670122', code=otp)  # The code user enters
        return verification_check.status
    except Exception as e:
        return "Try resending the OTP"
    

# send()
# verify()


def get_location_from_point(longitude, latitude):
    try:
        geolocator = Nominatim(user_agent="ayspm123@gmail.com")
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        logger.info(f"location from point : {location.address}")
        if location:
            address = location.raw.get("address", {})
        place = list(address.values())[0:2]
        place = ', '.join(place)
        return place
    except Exception as e:
        logger.error(f"Error from get_location_from_point, {e}")
        return ""


def send_templated_email(
    *,
    subject,
    recipient_list,
    heading=None,
    greeting="Hello,",
    intro=None,
    details=None,
    action_text=None,
    action_url=None,
    outro=None,
    signature="Team TiffinTrack",
    preheader=None,
    from_email=None,
    fail_silently=False,
):
    detail_items = []
    if isinstance(details, dict):
        detail_items = [{"label": str(k), "value": v} for k, v in details.items()]
    elif isinstance(details, (list, tuple)):
        for item in details:
            if isinstance(item, dict) and "label" in item and "value" in item:
                detail_items.append(item)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                detail_items.append({"label": str(item[0]), "value": item[1]})

    context = {
        "project_name": "TiffinTrack",
        "subject": subject,
        "heading": heading,
        "greeting": greeting,
        "intro": intro,
        "detail_items": detail_items,
        "action_text": action_text,
        "action_url": action_url,
        "outro": outro,
        "signature": signature,
        "preheader": preheader,
        "current_year": timezone.now().year,
    }

    text_body = render_to_string("emails/default_email.txt", context)
    html_body = render_to_string("emails/default_email.html", context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email or getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
        to=recipient_list,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=fail_silently)
