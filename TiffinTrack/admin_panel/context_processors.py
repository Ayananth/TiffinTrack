
from django.contrib.auth.decorators import login_required
from django.apps import apps
RestaurantProfile = apps.get_model("accounts", "RestaurantProfile")
def restaurant_requests(request):
    if request.user.is_authenticated and request.user.is_superuser:
        restaurant_requests = RestaurantProfile.objects.filter(is_approved=False).count()
        return {'restaurant_requests': restaurant_requests}
    return {'restaurant_requests': 0}