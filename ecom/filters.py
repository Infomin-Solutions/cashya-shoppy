from . import models
from django.contrib import admin


class OrderStatusFilter(admin.SimpleListFilter):
    title = 'Order Status'
    parameter_name = 'order_status'

    def lookups(self, request, model_admin):
        return [(status, status) for status in models.STATUS_CHOICES]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        else:
            return queryset
