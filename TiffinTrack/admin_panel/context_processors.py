
from django.contrib.auth.decorators import login_required
from restaurant.models import RestaurantProfile

def restaurant_requests(request):
    if request.user.is_authenticated and request.user.is_superuser:
        restaurant_requests = RestaurantProfile.objects.filter(is_approved=False).count()
        return {'restaurant_requests': restaurant_requests}
    return {'restaurant_requests': 0}