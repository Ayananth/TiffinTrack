from django.shortcuts import render, redirect, get_object_or_404
from .models import Coupon, CouponUsage
from users.models import Wallet
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import CouponForm, RestaurantCouponForm


from coupons.models import Coupon, CouponUsage
from django.views.decorators.http import require_POST
from restaurant.models import Subscriptions, RestaurantProfile
from django.contrib import messages


@require_POST
@login_required
def apply_coupon(request):
    subscription_id = request.POST.get('subscription_id')
    code = request.POST.get('coupon_code')
    print(f"{subscription_id=}")
    try:
        subscription = Subscriptions.objects.get(id=subscription_id)
        print(subscription)
    except Subscriptions.DoesNotExist:
        print("Item not found")
        messages.error(request, "Please try again! ")
        return redirect('user-home')
    try:
        coupon = Coupon.objects.get(code=code)
        if not coupon.is_valid():
            messages.error(request, "Coupon is invalid")
            return redirect('payment', id=subscription.id)
        if CouponUsage.objects.filter(user=request.user, coupon=coupon).count() >= coupon.usage_limit:
            messages.error(request, "Usage limit reached")
            return redirect('payment', id=subscription.id)
        if subscription.item_total < coupon.min_order_value:
            messages.error(request, f'Minimum order value is ₹{coupon.min_order_value}')
            return redirect('payment', id=subscription.id)
        # Log coupon usage
        CouponUsage.objects.create(user=request.user, coupon=coupon, subscription=subscription)
        subscription.coupon = coupon
        subscription.save()
        messages.success(request, "Coupon applied")
        return redirect('payment', id=subscription_id)
    except Coupon.DoesNotExist:
        messages.error(request, "Coupon code does not exists. ")
        return redirect('payment', id=subscription.id)



@login_required(login_url='login')
@require_POST
def remove_coupon(request):
    subscription_id = request.POST.get('subscription_id')
    try:
        subscription = Subscriptions.objects.get(id=subscription_id)
    except Subscriptions.DoesNotExist:
        messages.error(request, "Please try again! ")
        return redirect('payment', id=subscription_id)
    
    try:

        CouponUsage.objects.filter(user=request.user, coupon=subscription.coupon, subscription=subscription_id).delete()
        subscription.coupon = None
        subscription.save()
        messages.success(request, "Coupon removed")
        return redirect('payment', id=subscription_id)
    except Exception as e:
        messages.error(request,"Please try again")
        return redirect('payment', id=subscription_id)
    



@login_required(login_url='admin-login')
def coupon_form(request, coupon_id=None):
    if not request.user.is_superuser:
        return redirect('admin-login')
    if coupon_id:
        coupon = get_object_or_404(Coupon, id=coupon_id)
        action = "Edit"
    else:
        coupon = None
        action = "Create"
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, f"Coupon {action.lower()}ed successfully.")
            return redirect('admin-coupons')  # replace with your list view
    else:
        form = CouponForm(instance=coupon)
    
    return render(request, './admin_panel/add_coupon.html', {'form': form})

@login_required(login_url='admin-login')
def delete_coupon(request, coupon_id):
    if not request.user.is_superuser:
        return redirect('admin-login')
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, "Coupon deleted successfully.")
    return redirect('admin-coupons')  # Replace with your actual list view



#coupon, restaurants


@login_required(login_url='login')
def restaurant_coupon_form(request, coupon_id=None):
    if coupon_id:
        coupon = get_object_or_404(Coupon, id=coupon_id)
        action = "Edit"
    else:
        coupon = None
        action = "Create"
    
    if request.method == 'POST':
        form = RestaurantCouponForm(request.POST, instance=coupon)
        if form.is_valid():
            data = form.save(commit=False)
            data.save()  # Save first before setting M2M fields
            data.restaurant.set([request.user.restaurantprofile])  
            messages.success(request, f"Coupon {action.lower()}ed successfully.")
            return redirect('restaurant-coupons')  # replace with your list view
    else:
        form = RestaurantCouponForm(instance=coupon)
    
    return render(request, './restaurant/add_coupon.html', {'form': form})

@login_required(login_url='login')
def restaurant_delete_coupon(request, coupon_id):
    if request.user.user_type != 'restaurant':
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('restaurant-home')

    restaurant = get_object_or_404(RestaurantProfile, user=request.user)
    coupon = get_object_or_404(Coupon, id=coupon_id)

    print(f"{coupon=}")

    if restaurant in coupon.restaurant.all():
        coupon.restaurant.remove(restaurant)
        messages.success(request, "Coupon removed from your restaurant.")
    else:
        messages.warning(request, "This coupon is not associated with your restaurant.")

    return redirect('restaurant-coupons')