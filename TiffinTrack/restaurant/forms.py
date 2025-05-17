from django import forms
from .models import RestaurantProfile, MenuCategory

class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = RestaurantProfile
        fields = ['restaurant_name', 'owner_name', 'licence_no', 'contact_number', 
                  'email','restaurant_image' ]



class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['name']