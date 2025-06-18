from django import forms
from accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from restaurant.models import RestaurantProfile, FoodItem, MenuCategory, FoodCategory
from django.db.models import DateField, DateTimeField
from django.contrib.gis.geos import Point
from users.models import OrderReport


class AdminUserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'user_type', 'is_staff', 'is_active', 'is_blocked']



    def clean(self):    
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
    





class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = CustomUser
        fields = '__all__'


class RestaurantRegisterForm(forms.ModelForm):
    class Meta:
        model = RestaurantProfile
        fields = '__all__'
    point = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Search location...',
        'id': 'id_point',
        'autocomplete': 'off'
    }))
    def clean_point(self):
        value = self.cleaned_data['point']
        try:
            lon, lat = map(float, value.split(','))
            return Point(lon, lat)
        except Exception:
            raise forms.ValidationError("Invalid format for coordinates. Expected 'longitude,latitude'.")

class FoodItemManageForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = '__all__'

class FoodCategoryManageForm(forms.ModelForm):
    class Meta:
        model = FoodCategory
        fields = '__all__'
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'cancellation_time': forms.TimeInput(attrs={'type': 'time'}),
        }




class MenuManageForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = '__all__'




class ComplaintsForm(forms.ModelForm):
    class Meta:
        model = OrderReport
        fields = '__all__'
