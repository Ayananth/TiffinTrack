from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)



@register.filter
def km(distance, precision=2):
    """
    Converts a GeoDjango Distance object to kilometers with optional precision.
    Usage: {{ restaurant.distance|km }} or {{ restaurant.distance|km:1 }}
    """
    if distance is None:
        return ""
    try:
        return f"{distance.km:.{precision}f} km"
    except AttributeError:
        return str(distance)