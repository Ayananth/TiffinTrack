from accounts.utils import get_location_from_point

def location_context(request):
    user = request.user
    if user.is_authenticated:
        reference_point = user.profile.point
        longitude = reference_point.x
        latitude = reference_point.y
        location = get_location_from_point(longitude, latitude)
    else:
        location = None
    return {
        'location': location,
    }