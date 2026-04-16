from django import forms
from django.db.models import Case, IntegerField, Value, When
from .models import RestaurantProfile, MenuCategory, FoodItem, FoodCategory, Review, Day
from django.contrib.gis.geos import Point


class RestaurantProfileForm(forms.ModelForm):
    class Meta:
        model = RestaurantProfile
        fields = [
            "restaurant_name",
            "owner_name",
            "licence_no",
            "contact_number",
            "email",
            "restaurant_image",
            "address",
            "point",
        ]

    point = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search location...",
                "id": "id_point",
                "autocomplete": "off",
            }
        )
    )

    def clean_point(self):
        value = self.cleaned_data["point"]
        try:
            lon, lat = map(float, value.split(","))
            return Point(lon, lat)
        except Exception:
            raise forms.ValidationError(
                "Invalid format for coordinates. Expected 'longitude,latitude'."
            )


class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ["name"]


class FoodItemManageForm(forms.ModelForm):
    class Meta:
        model = FoodItem
        exclude = ["restaurant"]
        widgets = {
            "days": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop("restaurant", None)
        super().__init__(*args, **kwargs)

        weekday_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        for day_name in weekday_names:
            Day.objects.get_or_create(name=day_name)
        weekday_order = Case(
            *[
                When(name=day, then=Value(index))
                for index, day in enumerate(weekday_names)
            ],
            output_field=IntegerField(),
        )
        self.fields["days"].queryset = (
            Day.objects.filter(name__in=weekday_names)
            .annotate(_weekday_order=weekday_order)
            .order_by("_weekday_order")
        )

        if restaurant:
            self.fields["food_category"].queryset = FoodCategory.objects.filter(
                restaurant=restaurant
            )
            self.fields["food_category"].label_from_instance = lambda obj: (
                f"{obj.name}_{obj.menu_category.name}"
                if obj.menu_category
                else f"{obj.name}_No Menu"
            )

        # Menu category is derived from selected food category in the view.
        self.fields.pop("menu_category", None)


class MenuManageForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        exclude = ["restaurant"]


class FoodCategoryManageForm(forms.ModelForm):
    class Meta:
        model = FoodCategory
        exclude = ["restaurant"]

        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "cancellation_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop("restaurant", None)
        super().__init__(*args, **kwargs)

        if restaurant:
            self.fields["menu_category"].queryset = MenuCategory.objects.filter(
                restaurant=restaurant
            )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment", "description"]
        widgets = {
            "rating": forms.NumberInput(
                attrs={
                    "min": 1,
                    "max": 5,
                    "class": "form-control",
                    "placeholder": "Rating (1 to 5)",
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Write your comment...",
                    "rows": 3,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Detailed description (optional)",
                    "rows": 4,
                }
            ),
        }
        labels = {
            "rating": "Your Rating",
            "comment": "Short Comment",
            "description": "Detailed Review (optional)",
        }


from .models import Offer


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            "name",
            "description",
            "discount_percent",
            "valid_from",
            "valid_until",
            "menu_categories",
            "is_active",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_until": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "menu_categories": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop("restaurant", None)
        super().__init__(*args, **kwargs)
        if restaurant:
            self.fields["menu_categories"].queryset = MenuCategory.objects.filter(
                restaurant=restaurant, is_active=True
            )
