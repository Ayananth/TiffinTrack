# payments/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('pay/', views.initiate_payment, name='initiate_payment'),
    path('payment-handler/', views.payment_handler, name='payment_handler'),

]
