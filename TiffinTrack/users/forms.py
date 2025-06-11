
from django import forms
from django.utils import timezone
from restaurant.models import Subscriptions
from .models import Address


class SubscriptionForm(forms.ModelForm):
    use_wallet = forms.BooleanField(required=False)


    class Meta:
        model = Subscriptions
        fields = ['start_date', 'end_date', 'address']

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        today = timezone.now().date()
        if start:
            # Convert start to date if it's a datetime object
            start_date_only = start.date() if isinstance(start, timezone.datetime) else start
            if start_date_only < today:
                self.add_error('start_date', "Start date cannot be in the past.")

        if start and end:
            if start >= end:
                self.add_error('end_date', "End date must be after start date.")




class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['name', 'phone', 'address_line', 'landmark', 'city', 'state', 'pincode','is_default']

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


# forms.py

from .models import RestaurantReport

class RestaurantReportForm(forms.ModelForm):
    class Meta:
        model = RestaurantReport
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your report here...'})
        }
