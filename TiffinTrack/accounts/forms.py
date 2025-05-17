from django import forms
from .models import CustomUser, UserProfile
from django.contrib.auth.forms import UserCreationForm
from .models import Locations

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
    

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        location = forms.ModelChoiceField(
            queryset=Locations.objects.all(),
            empty_label="Select Location",
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        fields = [ 'profile_pic']
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("username") == "":
            raise forms.ValidationError("Username cannot be empty.")
        return cleaned_data
    
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone']