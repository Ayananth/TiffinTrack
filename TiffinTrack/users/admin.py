from django.contrib import admin
from .models import Address, Orders, Wallet, WalletTransaction, RestaurantReport

# Register your models here.

admin.site.register(Address)
admin.site.register(Orders)
admin.site.register(Wallet)
admin.site.register(WalletTransaction)
admin.site.register(RestaurantReport)




