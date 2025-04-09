from django.shortcuts import render, redirect
from .utils import login_redirect_view
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import PhoneOTP
from django.utils import timezone
from users.models import CustomUser
from datetime import timedelta
from .forms import UserRegisterForm



#TODO dont give access to admin
OTP_EXPIRY_SECONDS = 1000  # 5 minutes

def accounts_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(login_redirect_view(request))
        else:
            print("Invalid credentials")
            messages.success(request, "Invalid username or password")
    return render(request, './accounts/login.html')

def accounts_sign_up(request):
    print("register")
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

        otp_obj, created = PhoneOTP.objects.get_or_create(phone=phone)
        otp_obj.generate_otp()

        # TODO: Replace with Twilio
        print(f"OTP for {phone} is {otp_obj.otp}")

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

        try:
            otp_obj = PhoneOTP.objects.get(phone=phone)

            if otp_obj.otp == entered_otp:
                otp_obj.is_verified = True
                otp_obj.save()

                # Clear session and login
                request.session.pop('otp_sent', None)
                request.session.pop('otp_sent_time', None)
                request.session.pop('phone', None)

                user, created = CustomUser.objects.get_or_create(username=phone)
                login(request, user)
                return redirect("user-home")

            return render(request, "./accounts/verify_otp.html", {"error": "Incorrect OTP!"})

        except PhoneOTP.DoesNotExist:
            return redirect("send_otp")

    return render(request, "./accounts/verify_otp.html")