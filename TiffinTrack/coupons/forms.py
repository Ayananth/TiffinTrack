from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'cashback_amount', 'min_order_value', 'valid_from',
            'valid_to', 'active', 'usage_limit', 'restaurant'
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class RestaurantCouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'cashback_amount', 'min_order_value', 'valid_from',
            'valid_to', 'active', 'usage_limit'
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }