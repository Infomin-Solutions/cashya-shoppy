import sys
from . import models
from django.contrib import admin

# Register your models here.


@admin.register(models.SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['site_name']
    fieldsets = (
        ('General', {
            'fields': ('site_name', )
        }),
        ('Payment Gateway', {
            'fields': ('pg_charge', 'collect_from_customer')
        }),
        ('Payment Gateway Feature Flags', {
            'fields': ('enable_cod', 'enable_phonepe', 'enable_razorpay', 'enable_paytm'),
            'description': 'Configure which payment options are available to customers'
        })
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
