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





#TODO dont give access to admin
OTP_EXPIRY_SECONDS = 600  # 5 minutes

def accounts_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username, password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(login_redirect_view(request))
        else:
            print("Invalid credentials")
            messages.error(request, "Invalid username or password")
    return render(request, './accounts/login.html')

def accounts_logout(request):
    logout(request)
    request.session.flush() 
    return redirect('user-home')

def accounts_sign_up(request):
    print("register")
    username = request.POST.get("username")
    password = request.POST.get("password")
    print(username, password)

    referral = request.GET.get('ref')
    if referral:
        request.session['referral_code'] = referral


    if request.method == 'POST':
        print("post req")

        form = UserRegisterForm(request.POST) 
        if form.is_valid():
            print("form not valid")
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username}! Try login")
            return redirect('login')
        else:
            print("form not valid")
            print(form.errors)
            messages.error(request, "Form not valid")   
    else:
        print("Else")
        form = UserRegisterForm()
    context = {  
        'form':form  
    } 
    return render(request, './accounts/sign-up.html', context)



def send_otp(request):


    if request.session.get('otp_sent'):
        return redirect('verify_otp')

    phone = request.session.get('phone') or request.POST.get('phone')
    print(f"{phone=}")

    if request.method == 'POST' or phone:
        if not phone or not phone.isdigit() or len(phone) != 10:
            messages.error(request, "Invalid phone number")
            return render(request, "./accounts/send_otp.html")

        # otp_obj, created = PhoneOTP.objects.get_or_create(phone=phone)
        # otp_obj.generate_otp()
        status = send_otp_sms()
        if status == "failed":
            print("OTP failed")
            messages.error(request, "Please try again!")
            return render(request, "./accounts/send_otp.html")
            
        print("OTP sent")

        # TODO: Replace with Twilio
        # print(f"OTP for {phone} is {otp_obj.otp}")

        request.session['phone'] = phone
        request.session['otp_sent'] = True
        request.session['otp_sent_time'] = timezone.now().isoformat()

        return redirect('verify_otp')

    return render(request, "./accounts/send_otp.html")


def verify_otp(request):

    phone = request.session.get('phone')
    otp_sent = request.session.get('otp_sent')
    sent_time_str = request.session.get('otp_sent_time')

    # Check if required session keys exist
    if not phone or not otp_sent or not sent_time_str:
        messages.error(request, "Session expired. Please request OTP again.")
        return redirect('send_otp')

    # Parse ISO time and calculate expiry
    sent_time = timezone.datetime.fromisoformat(sent_time_str)
    now = timezone.now()
    if now - sent_time > timedelta(seconds=OTP_EXPIRY_SECONDS):
        # Clear expired session keys
        request.session.pop('otp_sent', None)
        request.session.pop('otp_sent_time', None)
        request.session.pop('phone', None)
        return render(request, "./accounts/verify_otp.html", {"error": "OTP expired. Please request again."})

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
                print(f"{e=}")
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
        print("sending mail")
        try:
            send_mail(
                "Email Confirmation",
                f"Click here to confirm the password: {confirm_url}",
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                fail_silently=False  # Force errors to show
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        print("mail send")
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
            subject="Confirm Password Change",
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