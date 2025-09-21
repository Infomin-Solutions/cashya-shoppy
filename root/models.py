import sys
from django.db import models

# Create your models here.


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=255, default='Cashya Shoppy')
    pg_charge = models.FloatField(default=2.0)
    collect_from_customer = models.BooleanField(default=False)

    # Payment Gateway Feature Flags
    enable_cod = models.BooleanField(
        default=True,
        verbose_name="Enable Cash on Delivery",
        help_text="Allow customers to pay via Cash on Delivery"
    )
    enable_phonepe = models.BooleanField(
        default=True,
        verbose_name="Enable PhonePe Gateway",
        help_text="Allow customers to pay using PhonePe"
    )
    enable_razorpay = models.BooleanField(
        default=True,
        verbose_name="Enable Razorpay Gateway",
        help_text="Allow customers to pay using Razorpay"
    )
    enable_paytm = models.BooleanField(
        default=True,
        verbose_name="Enable Paytm Gateway",
        help_text="Allow customers to pay using Paytm"
    )

    def __str__(self):
        return self.site_name
