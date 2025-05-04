from django import forms
from accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from restaurant.models import RestaurantProfile, FoodItem, MenuCategory, FoodCategory

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

class FoodItemManageForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        fields = '__all__'

class FoodCategoryManageForm(forms.ModelForm):
    class Meta:
        model = FoodCategory
        fields = '__all__'

class MenuManageForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = '__all__'




