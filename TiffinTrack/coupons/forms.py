from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Coupon


class BaseCouponForm(forms.ModelForm):
    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().upper()
        if not code:
            raise ValidationError("Coupon code is required.")
        if len(code) < 4:
            raise ValidationError("Coupon code must be at least 4 characters long.")
        if not code.replace("-", "").replace("_", "").isalnum():
            raise ValidationError(
                "Coupon code can only contain letters, numbers, '-' and '_'."
            )

        duplicate_qs = Coupon.objects.filter(code__iexact=code)
        if self.instance and self.instance.pk:
            duplicate_qs = duplicate_qs.exclude(pk=self.instance.pk)
        if duplicate_qs.exists():
            raise ValidationError("A coupon with this code already exists.")
        return code

    def clean(self):
        cleaned_data = super().clean()
        cashback_amount = cleaned_data.get("cashback_amount")
        min_order_value = cleaned_data.get("min_order_value")
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")
        usage_limit = cleaned_data.get("usage_limit")

        if cashback_amount is not None and cashback_amount <= 0:
            self.add_error("cashback_amount", "Cashback amount must be greater than 0.")

        if min_order_value is not None and min_order_value < 0:
            self.add_error("min_order_value", "Minimum order value cannot be negative.")

        if (
            cashback_amount is not None
            and min_order_value is not None
            and min_order_value > 0
            and cashback_amount > min_order_value
        ):
            self.add_error(
                "cashback_amount",
                "Cashback amount cannot be greater than minimum order value.",
            )

        if usage_limit is not None and usage_limit < 1:
            self.add_error("usage_limit", "Usage limit must be at least 1.")

        if valid_from and valid_to and valid_from >= valid_to:
            self.add_error("valid_to", "Valid to date must be after valid from date.")

        # Restrict creating new coupons in the past.
        if not self.instance.pk and valid_from and valid_from < timezone.now():
            self.add_error("valid_from", "Valid from date cannot be in the past.")

        return cleaned_data


class CouponForm(BaseCouponForm):
    class Meta:
        model = Coupon
        fields = [
            "code",
            "cashback_amount",
            "min_order_value",
            "valid_from",
            "valid_to",
            "active",
            "usage_limit",
            "restaurant",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_to": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class RestaurantCouponForm(BaseCouponForm):
    class Meta:
        model = Coupon
        fields = [
            "code",
            "cashback_amount",
            "min_order_value",
            "valid_from",
            "valid_to",
            "active",
            "usage_limit",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_to": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
