import sys
from . import models
from django.contrib import admin

# Register your models here.


if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv and models.SiteSetting.objects.count() == 0:
    models.SiteSetting.objects.create()


@admin.register(models.SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['site_name']
    fieldsets = (
        ('General', {
            'fields': ('site_name', )
        }),
        ('Payment Gateway', {
            'fields': ('pg_charge', 'collect_from_customer')
        })
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
