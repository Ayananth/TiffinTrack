from django import forms
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
        if start and end and start >= end:
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
