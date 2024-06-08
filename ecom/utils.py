from . import models


def calculate_discount(cart: models.Cart):
    if cart.coupon and cart.coupon.is_valid(cart.sub_total):
        if cart.coupon.coupon_type == 'percentage':
            return round(cart.sub_total * cart.coupon.discount / 100, 2)
        return round(cart.coupon.discount, 2)
    return 0


def calculate_shipping(cart: models.Cart):
    return 0


def calculate_tax(cart: models.Cart):
    return 0


def calculate_total(cart: models.Cart):
    return round(cart.sub_total - calculate_discount(cart) + calculate_shipping(cart) + calculate_tax(cart), 2)
