from typing import Any
from django.contrib import admin
from django.http.request import HttpRequest
from . import models
from . import forms
from . import filters

# Register your models here.


@admin.register(models.Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'image']


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


class ProductImageInline(admin.TabularInline):
    model = models.ProductImage
    extra = 0
    min_num = 1


class ProductVariantInline(admin.TabularInline):
    model = models.ProductVariant
    extra = 0
    min_num = 1


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'variants_count', 'category', 'images_count', 'available']
    inlines = [ProductImageInline, ProductVariantInline]

    def images_count(self, obj):
        return obj.images.count()
    images_count.short_description = 'Images'
    images_count.admin_order_field = 'images'

    def variants_count(self, obj):
        return obj.variants.count()
    variants_count.short_description = 'Variants'
    variants_count.admin_order_field = 'variants'


class CartItemInline(admin.TabularInline):
    model = models.CartItem
    extra = 0
    min_num = 1


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'cart_items_count', 'cart_price']
    inlines = [CartItemInline]

    def cart_items_count(self, obj):
        return obj.product_variants.count()
    cart_items_count.short_description = 'Cart Items'
    cart_items_count.admin_order_field = 'product_variants'

    def cart_price(self, obj):
        total = 0
        for item in models.CartItem.objects.filter(cart=obj):
            total += item.product_variant.price * item.quantity
        return total
    cart_price.short_description = 'Cart Price'
    cart_price.admin_order_field = 'product_variants'


class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    exclude = ['product_variant']
    extra = 0
    min_num = 1


class OrderStatusInline(admin.TabularInline):
    model = models.OrderStatus
    form = forms.OrderStatusInlineForm
    readonly_fields = ['created_at']
    extra = 0
    min_num = 1

    def get_max_num(self, request, obj, **kwargs):
        if obj:
            return obj.statuses.count() + 1
        return 1


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'created_at', 'status']
    readonly_fields = ['id', 'created_at', 'status']
    inlines = [OrderItemInline, OrderStatusInline]
    search_fields = ['id', 'user__username']
    list_filter = ['created_at', filters.OrderStatusFilter]

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if obj and not request.user.is_superuser:
            return fields + ['user', 'total']
        return fields


@admin.register(models.Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount', 'coupon_type', 'valid_from', 'valid_to', 'active', 'quantity']
    search_fields = ['code']


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'nickname', 'default', 'name']
