from accounts.utils import get_location_from_point

def location_context(request):
    user = request.user
    if user.is_authenticated:
        location = user.profile.location_name
    else:
        location = ""
    return {
        'location': location,
    }