import sys
import os
from django.db import models
from django.core.exceptions import ValidationError

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
        default=False,
        verbose_name="Enable PhonePe Gateway",
        help_text="Allow customers to pay using PhonePe (requires PHONEPE_MERCHANT_ID and PHONEPE_SALT_KEY)"
    )
    enable_razorpay = models.BooleanField(
        default=False,
        verbose_name="Enable Razorpay Gateway",
        help_text="Allow customers to pay using Razorpay (requires RAZORPAY_API_KEY and RAZORPAY_API_SECRET)"
    )
    enable_paytm = models.BooleanField(
        default=False,
        verbose_name="Enable Paytm Gateway",
        help_text="Allow customers to pay using Paytm (requires PAYTM_MID and PAYTM_MERCHANT_KEY)"
    )

    def clean(self):
        """Validate that required environment variables are present when enabling gateways."""
        errors = {}

        # Validate PhonePe environment variables
        if self.enable_phonepe:
            missing_phonepe = []
            if not os.getenv('PHONEPE_MERCHANT_ID'):
                missing_phonepe.append('PHONEPE_MERCHANT_ID')
            if not os.getenv('PHONEPE_SALT_KEY'):
                missing_phonepe.append('PHONEPE_SALT_KEY')
            if not os.getenv('PHONEPE_SALT_INDEX'):
                missing_phonepe.append('PHONEPE_SALT_INDEX')

            if missing_phonepe:
                errors['enable_phonepe'] = ValidationError(
                    f'Cannot enable PhonePe. Missing environment variables: {", ".join(missing_phonepe)}'
                )

        # Validate Razorpay environment variables
        if self.enable_razorpay:
            missing_razorpay = []
            if not os.getenv('RAZORPAY_API_KEY'):
                missing_razorpay.append('RAZORPAY_API_KEY')
            if not os.getenv('RAZORPAY_API_SECRET'):
                missing_razorpay.append('RAZORPAY_API_SECRET')

            if missing_razorpay:
                errors['enable_razorpay'] = ValidationError(
                    f'Cannot enable Razorpay. Missing environment variables: {", ".join(missing_razorpay)}'
                )

        # Validate Paytm environment variables
        if self.enable_paytm:
            missing_paytm = []
            if not os.getenv('PAYTM_MID'):
                missing_paytm.append('PAYTM_MID')
            if not os.getenv('PAYTM_SECRET'):
                missing_paytm.append('PAYTM_SECRET')

            if missing_paytm:
                errors['enable_paytm'] = ValidationError(
                    f'Cannot enable Paytm. Missing environment variables: {", ".join(missing_paytm)}'
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.site_name
