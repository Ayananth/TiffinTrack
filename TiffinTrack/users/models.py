from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.geos import Point
from restaurant.models import FoodCategory, FoodItem, RestaurantProfile, Subscriptions
import logging
logger = logging.getLogger('myapp') 
from cloudinary_storage.storage import MediaCloudinaryStorage


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def credit(self, amount, description=""):
        """Add money to wallet"""
        self.balance += amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='credit',
            description=description
        )

    def debit(self, amount, description=""):
        """Use money from wallet"""
        if amount > self.balance:
            raise ValueError("Insufficient wallet balance.")
        self.balance -= amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='debit',
            description=description
        )

    def __str__(self):
        return f"{self.user.username}'s Wallet – ₹{self.balance}"

class WalletTransaction(models.Model):
    TRANSACTION_CHOICES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=6, choices=TRANSACTION_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} ₹{self.amount} on {self.created_at.strftime('%Y-%m-%d')}"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='address')
    name = models.CharField(max_length=100)  # Name of recipient
    phone = models.CharField(max_length=15)  # Contact number
    address_line = models.CharField("House/Flat/Building", max_length=255)
    landmark = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ['-is_default', 'created_at']

    def __str__(self):
        return f"{self.name}, {self.address_line}, {self.city} - {self.pincode}"




class Orders(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='received_orders',
    )
    food_category = models.ForeignKey(
        FoodCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    food_item = models.ForeignKey(
        FoodItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    refund_issued = models.BooleanField(default=False)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    subscription_id = models.ForeignKey(Subscriptions, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)


    def cancel(self):
        if self.status != 'PENDING':
            logger.error("Error: order already cancelled")
            return False  # Cannot cancel delivered or already cancelled orders

        if self.refund_issued:
            logger.error("Error: Refund already processed")
            return False  # Refund already processed

        # Update status
        self.status = 'CANCELLED'
        self.refund_issued = True
        self.save()

        # Refund to wallet
        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.credit(self.food_category.price, description=f"Refund for cancelled order #{self.id}")

        return True

    def __str__(self):
        return f"Order #{self.id} by {self.user} from {self.restaurant}"


class RestaurantReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.user} on {self.restaurant}"
    
    
class OrderReport(models.Model):

    STATUS_CHOICES = [
        ('REFUNDED', 'Refunded'),
        ('REJECTED', 'Rejected'),
        ('PENDING', 'Pending'),
    ]



    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(RestaurantProfile, on_delete=models.CASCADE)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    image = models.ImageField(storage=MediaCloudinaryStorage(),
                                    upload_to='tiffintrack/prod/complaints/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolve_message = models.CharField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.user} on {self.restaurant}, order {self.order}"