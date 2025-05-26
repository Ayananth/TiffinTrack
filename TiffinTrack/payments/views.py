# payments/views.py

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
import razorpay
from .models import Payment
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.urls import reverse
from django.contrib import messages
from restaurant.models import Subscriptions


client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def initiate_payment(request):

    subscription = request.session.get('subscription')
    if not subscription:
        messages.error("Session expired, Please try again")
        return redirect('home')
    subscription = get_object_or_404(Subscriptions, id=int(subscription))  
    currency = 'INR'
    amount = subscription.paid_total_amount
    print(f"{amount=}")
    amount = amount*100

    razorpay_order = client.order.create({
        "amount": amount,
        "currency": currency,
        "payment_capture": '1'
    })

    payment = Payment.objects.create(
        user=request.user,
        amount=amount / 100,
        razorpay_order_id=razorpay_order['id']
    )

    context = {
        'order_id': razorpay_order['id'],
        'amount': amount,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'callback_url': reverse('payment_handler'),
    }

    return render(request, 'payments/payment_page.html', context)

@csrf_exempt
def payment_handler(request):
    if request.method == "POST":
        print("Post request========")
        try:
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            # Verify signature (optional but recommended)
            client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })
            payment = Payment.objects.get(razorpay_order_id=order_id)
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.status = 'paid'
            payment.save()
            


            # return render(request, 'payments/payment_success.html')
            return redirect('order-confirm')
        except Exception as e:
            return render(request, 'payments/payment_failed.html')

    else:
        return render(request, 'payments/payment_failed.html')

    
