from django.contrib import admin
from .models import CustomUser, Locations, UserProfile, RestaurantProfile

# Register your models here.
admin.site.register(CustomUser)
# admin.site.register(RestaurantProfile)
admin.site.register(Locations)



from django.contrib.gis.admin import GISModelAdmin
from django.contrib import admin
from .models import RestaurantProfile, RestaurantImage

admin.site.register(RestaurantImage)

@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(GISModelAdmin):
    default_lon = 76.1626624  # center longitude
    default_lat = 10.436608   # center latitude
    default_zoom = 12         # zoom level
    map_height = 400          # optional
    map_width = 800           # optional

@admin.register(UserProfile)
class RestaurantProfileAdmin(GISModelAdmin):
    default_lon = 76.1626624  # center longitude
    default_lat = 10.436608   # center latitude
    default_zoom = 12         # zoom level
    map_height = 400          # optional
    map_width = 800           # optional

