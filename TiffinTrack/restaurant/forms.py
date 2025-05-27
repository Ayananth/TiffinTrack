from django import forms
from .models import RestaurantProfile, MenuCategory, FoodItem, FoodCategory, Review
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



class MenuManageForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        exclude = ['restaurant']


class FoodCategoryManageForm(forms.ModelForm):
    class Meta:
        model = FoodCategory
        exclude = ['restaurant']

        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'cancellation_time': forms.TimeInput(attrs={'type': 'time'}),
        }



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'description']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1, 'max': 5, 'class': 'form-control', 'placeholder': 'Rating (1 to 5)'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Write your comment...', 'rows': 3
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'placeholder': 'Detailed description (optional)', 'rows': 4
            }),
        }
        labels = {
            'rating': 'Your Rating',
            'comment': 'Short Comment',
            'description': 'Detailed Review (optional)',
        }