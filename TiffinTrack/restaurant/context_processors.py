from .models import RestaurantProfile

def has_restaurant(request):
    """Returns a flag indicating if the logged-in user owns a restaurant."""
    if request.user.is_authenticated:
        return {"has_restaurant": RestaurantProfile.objects.filter(user=request.user, is_approved=True).exists()}
    return {"has_restaurant": False}