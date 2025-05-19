from django import forms
from .models import RestaurantProfile, MenuCategory, FoodItem, FoodCategory
from django.contrib.gis.geos import Point


class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = RestaurantProfile
        fields = ['restaurant_name', 'owner_name', 'licence_no', 'contact_number', 
                  'email','restaurant_image','address', 'point']
    point = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Search location...',
        'id': 'id_point',
        'autocomplete': 'off'
    }))
    def clean_point(self):
        value = self.cleaned_data['point']
        print("Raw point field value received:", value)
        try:
            lon, lat = map(float, value.split(','))
            return Point(lon, lat)
        except Exception:
            raise forms.ValidationError("Invalid format for coordinates. Expected 'longitude,latitude'.")



class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['name']


class FoodItemManageForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        exclude = ['restaurant']