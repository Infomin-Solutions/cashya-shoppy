from django.utils import timezone
from rest_framework.serializers import ValidationError


def validate_coupon(cart, coupon=None):
    if not coupon:
        if cart.coupon:
            coupon = cart.coupon
        else:
            raise ValidationError('Invalid coupon')
    if not coupon.active or (coupon.quantity and coupon.quantity <= 0):
        raise ValidationError('Coupon is not available')
    if coupon.valid_from and coupon.valid_from > timezone.now():
        raise ValidationError('Coupon is not available yet')
    if coupon.valid_to and coupon.valid_to < timezone.now():
        raise ValidationError('Coupon has expired')
    if coupon.minimum_order_value and cart.sub_total < coupon.minimum_order_value:
        raise ValidationError(
            f"Minimum order value should be {coupon.minimum_order_value}")
    return coupon.code


def calculate_discount(cart):
    try:
        if cart.coupon and validate_coupon(cart):
            if cart.coupon.coupon_type == 'percentage':
                return round(cart.sub_total * cart.coupon.discount / 100, 2)
            return round(
                cart.coupon.discount if cart.sub_total - cart.coupon.discount > 0 else 1, 2)
        return 0
    except ValidationError:
        pass


def calculate_payment_fee(order_amount):
    pg_charge = 2 / 100  # 2% payment gateway charge
    fee_multiplier = 1 - pg_charge
    total_amount = order_amount / fee_multiplier
    return round(total_amount, 2)


def calculate_shipping(cart):
    return 0


def calculate_tax(cart):
    return 0


def calculate_total(cart):
    return round(cart.sub_total - calculate_discount(cart) + calculate_shipping(cart) + calculate_tax(cart), 2)
