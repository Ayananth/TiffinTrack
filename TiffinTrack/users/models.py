from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.gis.db import models as geomodels
from django.contrib.gis.geos import Point


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    point = geomodels.PointField(geography=True, default=Point(76.1626624, 10.436608))


    def __str__(self):
        return f"{self.user} address"
