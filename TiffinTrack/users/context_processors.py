from accounts.utils import get_location_from_point
from django.core.exceptions import ObjectDoesNotExist

def location_context(request):
    user = request.user
    location = ""
    if user.is_authenticated:
        try:
            location = user.profile.location_name
        except ObjectDoesNotExist:
            # Some users (e.g., admin/staff) may not have a UserProfile.
            location = ""
    return {
        'location': location,
    }
