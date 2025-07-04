from django.shortcuts import render, redirect
from .utils import login_redirect_view
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import PhoneOTP
from django.utils import timezone
from accounts.models import CustomUser
from datetime import timedelta
from .forms import UserRegisterForm
from .utils import send_otp_sms, verify_otp_sms
import os

import secrets
from django.core.mail import send_mail
from django.conf import settings


from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.urls import reverse
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import update_session_auth_hash

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


import logging
logger = logging.getLogger('myapp') 


#TODO dont give access to admin
OTP_EXPIRY_SECONDS = 600  # 5 minutes

def accounts_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(login_redirect_view(request))
        else:
            logger.warning("Invalid credentials")
            messages.error(request, "Invalid username or password")
    return render(request, './accounts/login.html')

def accounts_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('user-home')

def accounts_sign_up(request,id=None):

    if request.method != 'POST':

        if id:
            try:
                user = CustomUser.objects.get(id=id)
                form = UserRegisterForm(instance=user) 
                return render(request, './accounts/sign-up.html', {'form': form})
            except CustomUser.DoesNotExist:
                form = UserRegisterForm() 
                return render(request, './accounts/sign-up.html', {'form': form})
            

    username = request.POST.get("username")
    password = request.POST.get("password")

    try:
        user = CustomUser.objects.get(username=username)
        user.generate_otp()
        send_mail(
            subject='TiffinTrack Email Verification',
            message=f'Your OTP is: {user.otp}',
            from_email= os.environ.get('EMAIL_HOST_USER'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return redirect('verify_otp', user_id = user.id)

    except CustomUser.DoesNotExist:
        pass




    referral = request.GET.get('ref')
    if referral:
        request.session['referral_code'] = referral


    if request.method == 'POST':
        form = UserRegisterForm(request.POST) 
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email verified
            user.save()
            user.generate_otp()
            send_mail(
                subject='TiffinTrack Email Verification',
                message=f'Your OTP is: {user.otp}',
                from_email= os.environ.get('EMAIL_HOST_USER'),
                recipient_list=[user.email],
                fail_silently=False,
            )
            username = form.cleaned_data.get('username')
            return redirect('verify_otp', user_id=user.id)
        else:
            messages.error(request, "Form not valid")

    else:
        form = UserRegisterForm()
    context = {  
        'form':form  
    } 
    return render(request, './accounts/sign-up.html', context)



# def send_otp(request):


#     if request.session.get('otp_sent'):
#         return redirect('verify_otp')

#     phone = request.session.get('phone') or request.POST.get('phone')

#     if request.method == 'POST' or phone:
#         if not phone or not phone.isdigit() or len(phone) != 10:
#             messages.error(request, "Invalid phone number")
#             return render(request, "./accounts/send_otp.html")

#         status = send_otp_sms()
#         if status == "failed":
#             messages.error(request, "Please try again!")
#             return render(request, "./accounts/send_otp.html")

#         request.session['phone'] = phone
#         request.session['otp_sent'] = True
#         request.session['otp_sent_time'] = timezone.now().isoformat()

#         return redirect('verify_otp')

#     return render(request, "./accounts/send_otp.html")


def verify_otp(request, user_id):
    user = CustomUser.objects.get(id=user_id)

    if user.email_verified:
        return redirect('login')
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        action = request.POST.get("action")

        if action == "resend":
            request.session.pop('otp_sent', None)
            request.session.pop('otp_sent_time', None)
            return redirect('resend_otp', user_id=user.id)
        elif action == "edit_phone":
            request.session.pop('otp_sent', None)
            request.session.pop('otp_sent_time', None)
            request.session.pop('phone', None)
            return redirect('register', id=user.id)
        
        if user.otp == entered_otp and timezone.now() <= user.otp_created_at + timedelta(minutes=10):
            user.email_verified = True
            user.is_active = True
            user.otp = None
            user.save()
            
            messages.success(request, "Email verified successfully! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "Invalid or expired OTP.")
    
    return render(request, './accounts/verify_otp.html', {'user': user})



def resend_otp(request,user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error("Something went wrong, Please try again")
        return redirect('register')
    
    user.generate_otp()
    send_mail(
        subject='TiffinTrack Email Verification',
        message=f'Your OTP is: {user.otp}',
        from_email= os.environ.get('EMAIL_HOST_USER'),
        recipient_list=[user.email],
        fail_silently=False,
    )
    messages.success(request, f"OTP SENT")
    return redirect('verify_otp', user_id=user.id)
    






def verify_otp_sms(request):

    phone = request.session.get('phone')
    otp_sent = request.session.get('otp_sent')
    sent_time_str = request.session.get('otp_sent_time')

    # Check if required session keys exist
    # if not phone or not otp_sent or not sent_time_str:
    #     messages.error(request, "Session expired. Please request OTP again.")
    #     return redirect('send_otp')

    # Parse ISO time and calculate expiry
    # sent_time = timezone.datetime.fromisoformat(sent_time_str)
    now = timezone.now()
    # if now - sent_time > timedelta(seconds=OTP_EXPIRY_SECONDS):
    #     # Clear expired session keys
    #     request.session.pop('otp_sent', None)
    #     request.session.pop('otp_sent_time', None)
    #     request.session.pop('phone', None)
    #     return render(request, "./accounts/verify_otp.html", {"error": "OTP expired. Please request again."})

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        action = request.POST.get("action")

        if action == "resend":
            request.session.pop('otp_sent', None)
            request.session.pop('otp_sent_time', None)
            return redirect('send_otp')
        elif action == "edit_phone":
            request.session.pop('otp_sent', None)
            request.session.pop('otp_sent_time', None)
            request.session.pop('phone', None)
            return redirect('send_otp')

        otp_status = verify_otp_sms(entered_otp)
        if otp_status == "approved":
            # Clear session and login
            request.session.pop('otp_sent', None)
            request.session.pop('otp_sent_time', None)
            request.session.pop('phone', None)

            if CustomUser.objects.filter(phone=phone).exists():
                messages.error(request, "This number is already registered")
                return redirect('login')


            
            try:
                user, created = CustomUser.objects.get_or_create(username=phone, phone=phone)
            except Exception as e:
                messages.error(request, "Please try again")
                logger.warning("Verify otp error")
                logger.error(e)

                return redirect('login')

            login(request, user)
            return redirect("user-home")
            #TODO error message display
        else:
            return render(request, "./accounts/verify_otp.html", {"error": otp_status})

    return render(request, "./accounts/verify_otp.html")



@login_required
def request_email_change(request):
    if request.method == "POST":
        new_email = request.POST.get("new_email")
        # Check if email is already used
        if User.objects.filter(email__iexact=new_email).exclude(id=request.user.id).exists():
            messages.error(request, "This email is already in use.")
            return redirect('user-profile')
        try:
            validate_email(new_email)
        except ValidationError:
            messages.error(request, "Invalid email address.")
            return redirect('user-profile')
        user = request.user
        if new_email == user.email:
            messages.error(request, "No change in Email")
            return redirect('user-profile')
        
        token = secrets.token_urlsafe(32)
        user.pending_email = new_email
        user.email_change_token = token
        user.email_change_expiry = timezone.now() + timezone.timedelta(hours=24)
        user.save()

        confirm_url = request.build_absolute_uri(
            f"/accounts/confirm-email-change/?token={token}"
        )
        logger.info("sending mail")
        try:
            send_mail(
                "TiffinTrack-Email Confirmation",
                f"Click here to confirm the email: {confirm_url}",
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                fail_silently=False  # Force errors to show
            )
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
        logger.info("mail send")
        messages.success(request,"Confirmation email sent to your new email. Please check your inbox.")

    return redirect('user-profile')



# accounts/views.py
from django.http import HttpResponse

def confirm_email_change(request):
    token = request.GET.get("token")
    user = CustomUser.objects.filter(email_change_token=token).first()

    if not user or not user.email_change_expiry or user.email_change_expiry < timezone.now():
        return HttpResponse("Invalid or expired token.", status=400)

    user.email = user.pending_email
    user.pending_email = None
    user.email_change_token = None
    user.email_change_expiry = None
    user.save()

    messages.success(request, "")

    return HttpResponse("Your email has been successfully updated.")




User = get_user_model()
signer = TimestampSigner()

@login_required
def request_password_change(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")

        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect")
            return redirect('user-profile')
        
        try:
            validate_password(new_password, user=request.user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('user-profile')

        # Sign the data (user ID and new password)
        data = f"{request.user.id}:{new_password}"
        token = signer.sign(data)

        # Send confirmation email
        confirm_url = request.build_absolute_uri(
            reverse("confirm_password_change", args=[token])
        )
        send_mail(
            subject="TiffinTrack-Confirm Password Change",
            message=f"Click the link to confirm your password change:\n{confirm_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )


        messages.success(request,"Confirmation email sent to your new email. Please check your inbox.")

    return redirect('user-profile')




def confirm_password_change(request, token):
    try:
        data = signer.unsign(token, max_age=600)  # 10 minutes valid
        user_id, new_password = data.split(":")
        user = User.objects.get(id=user_id)
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return HttpResponse("Password changed successfully.")
    except (SignatureExpired, BadSignature, ValueError, User.DoesNotExist):
        return HttpResponse("Invalid or expired link.", status=400)