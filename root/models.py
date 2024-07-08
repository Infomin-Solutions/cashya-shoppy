import sys
from django.db import models

# Create your models here.


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=255, default='Cashya Shoppy')
    pg_charge = models.FloatField(default=2.0)
    collect_from_customer = models.BooleanField(default=False)

    def __str__(self):
        return self.site_name
