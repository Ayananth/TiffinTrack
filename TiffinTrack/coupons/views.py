from django.shortcuts import render
from .models import Coupon, CouponUsage
from users.models import Wallet
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


# Create your views here.


@login_required(login_url='login')
def apply_coupon(request):
    code = request.POST.get('coupon_code')
    order_amount = Decimal(request.POST.get('order_total'))

    try:
        coupon = Coupon.objects.get(code=code)
        if not coupon.is_valid():
            return JsonResponse({'error': 'Coupon is expired or inactive'})

        # Check if user already used it
        if CouponUsage.objects.filter(user=request.user, coupon=coupon).count() >= coupon.usage_limit:
            return JsonResponse({'error': 'Coupon usage limit reached'})

        if order_amount < coupon.min_order_value:
            return JsonResponse({'error': f'Minimum order value is ₹{coupon.min_order_value}'})

        # Log coupon usage
        CouponUsage.objects.create(user=request.user, coupon=coupon)

        return JsonResponse({'success': f'₹{coupon.cashback_amount} cashback added to total amount!'})

    except Coupon.DoesNotExist:
        return JsonResponse({'error': 'Invalid coupon code'})
