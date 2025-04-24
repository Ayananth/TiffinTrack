from django import forms
from accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm

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
