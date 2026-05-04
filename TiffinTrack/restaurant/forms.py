from django import forms
from django.db.models import Case, IntegerField, Value, When
from .models import RestaurantProfile, MenuCategory, FoodItem, FoodCategory, Review, Day
from django.contrib.gis.geos import Point
from django.utils.html import strip_tags
import re


class RestaurantProfileForm(forms.ModelForm):
    _WKT_POINT_RE = re.compile(
        r"^SRID=\d+;POINT\s*\(\s*[-+]?\d*\.?\d+\s+[-+]?\d*\.?\d+\s*\)$"
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance and getattr(instance, "pk", None):
            location_name = (instance.location_name or "").strip()
            if location_name:
                self.initial["point"] = location_name
            else:
                self.initial["point"] = ""

    @staticmethod
    def _parse_lon_lat(value):
        lon, lat = map(float, value.split(","))
        return Point(lon, lat)

    @classmethod
    def _is_wkt_point(cls, value):
        return bool(value and cls._WKT_POINT_RE.match(value.strip()))

    @staticmethod
    def _is_lon_lat_text(value):
        try:
            parts = [p.strip() for p in value.split(",")]
            if len(parts) != 2:
                return False
            float(parts[0])
            float(parts[1])
            return True
        except Exception:
            return False

    def clean_point(self):
        value = self.cleaned_data["point"].strip()
        selected_coords = (self.data.get("point_coords") or "").strip()
        selected_name = (self.data.get("point_display") or "").strip()

        # Preferred path: user picked a suggestion, we get coordinates from hidden input.
        if selected_coords:
            try:
                self._selected_location_name = selected_name or value
                return self._parse_lon_lat(selected_coords)
            except Exception:
                pass

        try:
            point = self._parse_lon_lat(value)
            self._selected_location_name = selected_name or getattr(
                self.instance, "location_name", ""
            )
            return point
        except Exception:
            # For existing restaurants, allow keeping current point when the field
            # contains a human-readable place name and location is not being changed.
            instance = getattr(self, "instance", None)
            if instance and getattr(instance, "pk", None) and instance.point:
                self._selected_location_name = (
                    selected_name
                    or instance.location_name
                    or ""
                )
                return instance.point
            raise forms.ValidationError(
                "Please select a location from suggestions so coordinates can be saved."
            )

    def save(self, commit=True):
        obj = super().save(commit=False)
        location_name = (getattr(self, "_selected_location_name", "") or "").strip()
        if (
            location_name
            and not self._is_wkt_point(location_name)
            and not self._is_lon_lat_text(location_name)
        ):
            obj.location_name = location_name
        if commit:
            obj.save()
            self.save_m2m()
        return obj


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
        self.restaurant = restaurant
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

    def clean(self):
        cleaned_data = super().clean()
        food_category = cleaned_data.get("food_category")
        days = cleaned_data.get("days")

        if not food_category or not days:
            return cleaned_data

        restaurant = self.restaurant or getattr(self.instance, "restaurant", None)
        if not restaurant:
            return cleaned_data

        conflicts = FoodItem.objects.filter(
            restaurant=restaurant,
            food_category=food_category,
            days__in=days,
        )
        if self.instance and self.instance.pk:
            conflicts = conflicts.exclude(pk=self.instance.pk)

        if conflicts.exists():
            conflicting_days = (
                Day.objects.filter(food_items__in=conflicts, id__in=[day.id for day in days])
                .values_list("name", flat=True)
                .distinct()
            )
            day_text = ", ".join(sorted(conflicting_days))
            self.add_error(
                "days",
                (
                    f"Only one food item is allowed for {food_category.name} on: {day_text}. "
                    "Please remove those days or edit the existing food item."
                ),
            )

        return cleaned_data


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
    _SCRIPT_LIKE_RE = re.compile(
        r"(<\s*script\b|javascript:|data:text/html)",
        re.IGNORECASE,
    )

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

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating

    def _validate_review_text(self, value, field_label):
        if not value:
            return value

        text = value.strip()
        if not text:
            return ""

        if strip_tags(text) != text or self._SCRIPT_LIKE_RE.search(text):
            raise forms.ValidationError(
                f"{field_label} contains invalid content. HTML/JS is not allowed."
            )
        return text

    def clean_comment(self):
        return self._validate_review_text(
            self.cleaned_data.get("comment"), "Comment"
        )

    def clean_description(self):
        return self._validate_review_text(
            self.cleaned_data.get("description"), "Description"
        )


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
