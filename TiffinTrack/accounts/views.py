from django.shortcuts import render, redirect
from .utils import (
    login_redirect_view,
    send_otp_sms,
    verify_otp_sms,
    send_templated_email,
)
from .utils import (
    login_redirect_view,
    send_otp_sms,
    verify_otp_sms,
    send_templated_email,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import PhoneOTP
from django.utils import timezone
from accounts.models import CustomUser
from datetime import timedelta
from .forms import UserRegisterForm
import os

import secrets
from django.conf import settings


from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.urls import reverse
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import update_session_auth_hash

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse


import logging

logger = logging.getLogger("myapp")


def _handle_view_error(request, view_name, redirect_name="login"):
    logger.exception("Error in %s", view_name)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
        return JsonResponse(
            {"success": False, "error": "Something went wrong. Please try again."},
            status=500,
        )
    messages.error(request, "Something went wrong. Please try again.")
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect(redirect_name)


# TODO dont give access to admin
# TODO dont give access to admin
OTP_EXPIRY_SECONDS = 600  # 5 minutes


def _login_context(is_restaurant=False):
    if is_restaurant:
        return {
            "auth_heading": "Welcome To TiffinTrack",
            "auth_subheading": "Log In Your Restaurant Account",
            "signup_url_name": "restaurant-register-auth",
            "signup_label": "Create Restaurant Account",
            "login_url_name": "restaurant-login",
        }
    return {
        "auth_heading": "Welcome To TiffinTrack",
        "auth_subheading": "Log In Your Account",
        "signup_url_name": "register",
        "signup_label": "Create Account",
        "login_url_name": "login",
    }


def _signup_context(is_restaurant=False):
    if is_restaurant:
        return {
            "signup_heading": "Create your restaurant account",
            "signup_subheading": "Enter your details to start restaurant onboarding",
            "login_url_name": "restaurant-login",
            "login_label": "Restaurant Login",
        }
    return {
        "signup_heading": "Create your account",
        "signup_subheading": "Enter your personal details to create account",
        "login_url_name": "login",
        "login_label": "Login",
    }


def _handle_login(request, required_user_type=None, is_restaurant=False):

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")

        user = None
        if email and password:
            existing_user = CustomUser.objects.filter(email__iexact=email).first()
            if existing_user:
                user = authenticate(
                    request, username=existing_user.username, password=password
                )

        if user is not None:
            if required_user_type and user.user_type != required_user_type:
                messages.error(request, "Please log in using the correct portal.")
                return render(
                    request,
                    "./accounts/login.html",
                    _login_context(is_restaurant=is_restaurant),
                )
            login(request, user)
            return redirect(login_redirect_view(request))
        else:
            logger.warning("Invalid credentials")
            messages.error(request, "Invalid email or password")
    return render(
        request, "./accounts/login.html", _login_context(is_restaurant=is_restaurant)
    )


def accounts_login(request):
    try:
        return _handle_login(request)
    except Exception:
        return _handle_view_error(request, "accounts_login")


def restaurant_login(request):
    try:
        return _handle_login(request, required_user_type="restaurant", is_restaurant=True)
    except Exception:
        return _handle_view_error(request, "restaurant_login")


def accounts_logout(request):
    try:
        logout(request)
        request.session.flush()
        return redirect("user-home")
    except Exception:
        return _handle_view_error(request, "accounts_logout")


def _handle_signup(request, id=None, user_type="normal", is_restaurant=False):

    if request.method != "POST":

        if id:
            try:
                user = CustomUser.objects.get(id=id, user_type=user_type)
                form = UserRegisterForm(instance=user)
                context = {"form": form}
                context.update(_signup_context(is_restaurant=is_restaurant))
                return render(request, "./accounts/sign-up.html", context)
            except CustomUser.DoesNotExist:
                form = UserRegisterForm()
                context = {"form": form}
                context.update(_signup_context(is_restaurant=is_restaurant))
                return render(request, "./accounts/sign-up.html", context)

    username = request.POST.get("username")
    try:
        user = CustomUser.objects.get(username=username, user_type=user_type)
        user.generate_otp()
        send_templated_email(
            subject="TiffinTrack Email Verification",
            recipient_list=[user.email],
            heading="Email Verification OTP",
            intro="Use the OTP below to verify your account.",
            details={
                "OTP": user.otp,
                "Valid For": "10 minutes",
            },
            preheader="Your verification code from TiffinTrack.",
            from_email=os.environ.get("EMAIL_HOST_USER"),
            fail_silently=False,
        )
        return redirect("verify_otp", user_id=user.id)

    except CustomUser.DoesNotExist:
        pass

    if user_type == "normal":
        referral = request.GET.get("ref")
        if referral:
            request.session["referral_code"] = referral

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = user_type
            user.is_active = False  # Deactivate until email verified
            user.save()
            user.generate_otp()
            send_templated_email(
                subject="TiffinTrack Email Verification",
                recipient_list=[user.email],
                heading="Email Verification OTP",
                intro="Use the OTP below to verify your account.",
                details={
                    "OTP": user.otp,
                    "Valid For": "10 minutes",
                },
                preheader="Your verification code from TiffinTrack.",
                from_email=os.environ.get("EMAIL_HOST_USER"),
                fail_silently=False,
            )
            username = form.cleaned_data.get("username")
            return redirect("verify_otp", user_id=user.id)
        else:
            messages.error(request, "Form not valid")

    else:
        form = UserRegisterForm()
    context = {"form": form}
    context.update(_signup_context(is_restaurant=is_restaurant))
    return render(request, "./accounts/sign-up.html", context)


def accounts_sign_up(request, id=None):
    try:
        return _handle_signup(request, id=id, user_type="normal", is_restaurant=False)
    except Exception:
        return _handle_view_error(request, "accounts_sign_up")


def restaurant_sign_up(request, id=None):
    try:
        return _handle_signup(request, id=id, user_type="restaurant", is_restaurant=True)
    except Exception:
        return _handle_view_error(request, "restaurant_sign_up")


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
    try:
        user = CustomUser.objects.get(id=user_id)
    
        if user.email_verified:
            return redirect("login")
    
        if request.method == "POST":
            entered_otp = request.POST.get("otp")
            action = request.POST.get("action")
    
            if action == "resend":
                request.session.pop("otp_sent", None)
                request.session.pop("otp_sent_time", None)
                return redirect("resend_otp", user_id=user.id)
            elif action == "edit_phone":
                request.session.pop("otp_sent", None)
                request.session.pop("otp_sent_time", None)
                request.session.pop("phone", None)
                if user.user_type == "restaurant":
                    return redirect("restaurant-register-auth", id=user.id)
                return redirect("register", id=user.id)
    
            if (
                user.otp == entered_otp
                and timezone.now() <= user.otp_created_at + timedelta(minutes=10)
            ):
                user.email_verified = True
                user.is_active = True
                user.otp = None
                user.save()
    
                messages.success(
                    request, "Email verified successfully! You can now log in."
                )
                if user.user_type == "restaurant":
                    return redirect("restaurant-login")
                return redirect("login")
            else:
                messages.error(request, "Invalid or expired OTP.")
    
        return render(request, "./accounts/verify_otp.html", {"user": user})
    except Exception:
        return _handle_view_error(request, "verify_otp")


def resend_otp(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        messages.error("Something went wrong, Please try again")
        return redirect("login")

    user.generate_otp()
    send_templated_email(
        subject="TiffinTrack Email Verification",
        recipient_list=[user.email],
        heading="Email Verification OTP",
        intro="Here is your new OTP for email verification.",
        details={
            "OTP": user.otp,
            "Valid For": "10 minutes",
        },
        preheader="Your new verification code from TiffinTrack.",
        from_email=os.environ.get("EMAIL_HOST_USER"),
        fail_silently=False,
    )
    messages.success(request, f"OTP SENT")
    return redirect("verify_otp", user_id=user.id)


def verify_otp_sms(request):

    try:
        phone = request.session.get("phone")
        otp_sent = request.session.get("otp_sent")
        sent_time_str = request.session.get("otp_sent_time")
    
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
                request.session.pop("otp_sent", None)
                request.session.pop("otp_sent_time", None)
                return redirect("send_otp")
            elif action == "edit_phone":
                request.session.pop("otp_sent", None)
                request.session.pop("otp_sent_time", None)
                request.session.pop("phone", None)
                return redirect("send_otp")
    
            otp_status = verify_otp_sms(entered_otp)
            if otp_status == "approved":
                # Clear session and login
                request.session.pop("otp_sent", None)
                request.session.pop("otp_sent_time", None)
                request.session.pop("phone", None)
    
                if CustomUser.objects.filter(phone=phone).exists():
                    messages.error(request, "This number is already registered")
                    return redirect("login")
    
                try:
                    user, created = CustomUser.objects.get_or_create(
                        username=phone, phone=phone
                    )
                except Exception as e:
                    messages.error(request, "Please try again")
                    logger.warning("Verify otp error")
                    logger.error(e)
    
                    return redirect("login")
    
                login(request, user)
                return redirect("user-home")
                # TODO error message display
            else:
                return render(request, "./accounts/verify_otp.html", {"error": otp_status})
    
        return render(request, "./accounts/verify_otp.html")
    except Exception:
        return _handle_view_error(request, "verify_otp_sms")


@login_required
def request_email_change(request):
    try:
        if request.method == "POST":
            new_email = request.POST.get("new_email")
            # Check if email is already used
            if (
                User.objects.filter(email__iexact=new_email)
                .exclude(id=request.user.id)
                .exists()
            ):
                messages.error(request, "This email is already in use.")
                return redirect("user-profile")
            try:
                validate_email(new_email)
            except ValidationError:
                messages.error(request, "Invalid email address.")
                return redirect("user-profile")
            user = request.user
            if new_email == user.email:
                messages.error(request, "No change in Email")
                return redirect("user-profile")
    
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
                send_templated_email(
                    subject="TiffinTrack - Email Confirmation",
                    recipient_list=[new_email],
                    heading="Confirm Your New Email Address",
                    intro="Please confirm your new email address using the button below.",
                    details={
                        "Requested By": request.user.username,
                        "New Email": new_email,
                        "Link Validity": "24 hours",
                    },
                    action_text="Confirm Email",
                    action_url=confirm_url,
                    preheader="Secure confirmation for your TiffinTrack email change request.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Email sending failed: {e}")
            logger.info("mail send")
            messages.success(
                request,
                "Confirmation email sent to your new email. Please check your inbox.",
            )
    
        return redirect("user-profile")
    except Exception:
        return _handle_view_error(request, "request_email_change")


# accounts/views.py
from django.http import HttpResponse


def confirm_email_change(request):
    try:
        token = request.GET.get("token")
        if not token:
            messages.error(request, "Invalid email confirmation link.")
            return redirect("user-profile")

        user = CustomUser.objects.filter(email_change_token=token).first()
    
        if (
            not user
            or not user.pending_email
            or not user.email_change_expiry
            or user.email_change_expiry < timezone.now()
        ):
            messages.error(request, "This email confirmation link is invalid or expired.")
            return redirect("user-profile")
    
        user.email = user.pending_email
        user.pending_email = None
        user.email_change_token = None
        user.email_change_expiry = None
        user.save()
    
        messages.success(request, "Your email has been updated successfully.")
        return redirect("user-profile")
    except Exception:
        return _handle_view_error(request, "confirm_email_change")


User = get_user_model()
signer = TimestampSigner()


@login_required
def request_password_change(request):
    try:
        if request.method == "POST":
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
    
            if not request.user.check_password(current_password):
                messages.error(request, "Current password is incorrect")
                return redirect("user-profile")
    
            try:
                validate_password(new_password, user=request.user)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return redirect("user-profile")
    
            # Sign the data (user ID and new password)
            data = f"{request.user.id}:{new_password}"
            token = signer.sign(data)
    
            # Send confirmation email
            confirm_url = request.build_absolute_uri(
                reverse("confirm_password_change", args=[token])
            )
            send_templated_email(
                subject="TiffinTrack - Confirm Password Change",
                recipient_list=[request.user.email],
                heading="Confirm Password Change",
                intro="We received a request to change your password.",
                details={
                    "User": request.user.username,
                    "Link Validity": "10 minutes",
                },
                action_text="Confirm Password Change",
                action_url=confirm_url,
                preheader="Security confirmation for your TiffinTrack account.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                fail_silently=False,
            )
    
            messages.success(
                request,
                "Confirmation email sent to your new email. Please check your inbox.",
            )
    
        return redirect("user-profile")
    except Exception:
        return _handle_view_error(request, "request_password_change")


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
