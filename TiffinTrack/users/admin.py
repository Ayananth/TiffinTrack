from django.contrib import admin
from .models import Address, Orders, Wallet, WalletTransaction

# Register your models here.

admin.site.register(Address)
admin.site.register(Orders)
admin.site.register(Wallet)
admin.site.register(WalletTransaction)




