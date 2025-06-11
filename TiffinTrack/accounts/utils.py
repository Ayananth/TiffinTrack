from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect
# utils/twilio_sms.py
from twilio.rest import Client
from django.conf import settings
from geopy.geocoders import Nominatim
import logging
logger = logging.getLogger('myapp') 



def login_redirect_view(request):
    user = request.user
    if user.is_normal_user:
        return reverse('user-home')
    elif user.is_restaurant_user:
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

