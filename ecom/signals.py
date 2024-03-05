
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from . import models

'''
The following function is used to update the denormalised order status field in the Order model.
'''


def order_status_change(instance: models.OrderStatus):
    order = instance.order
    status = order.get_status_choices()[0][1]
    order.status = status
    order.save()


@receiver(post_save, sender=models.OrderStatus)
def order_status_post_save(sender, instance: models.OrderStatus, **kwargs):
    order_status_change(instance)


@receiver(post_delete, sender=models.OrderStatus)
def order_status_post_delete(sender, instance: models.OrderStatus, **kwargs):
    order_status_change(instance)


'''
The following function is used to remove the cart items if the product or product variant is not available.
'''


def cart_product_available_check(sender, instance: models.Product):
    variants = models.ProductVariant.objects.filter(product=instance)
    if not instance.available:
        variants.update(available=False)
        models.CartItem.objects.filter(product_variant__in=variants).delete()
    else:
        unavailable_variants = variants.filter(available=False)
        models.CartItem.objects.filter(
            product_variant__in=unavailable_variants).delete()


@receiver(post_save, sender=models.Product)
def cart_product_available_check_post_save(sender, instance: models.Product, **kwargs):
    cart_product_available_check(instance)


@receiver(pre_delete, sender=models.Product)
def cart_product_available_check_post_delete(sender, instance: models.Product, **kwargs):
    instance.available = False
    cart_product_available_check(instance)


@receiver(post_save, sender=models.ProductVariant)
def cart_product_variant_available_check_post_save(sender, instance: models.ProductVariant, **kwargs):
    cart_product_available_check(instance.product)


@receiver(pre_delete, sender=models.ProductVariant)
def cart_product_variant_available_check_post_delete(sender, instance: models.ProductVariant, **kwargs):
    instance.product.available = False
    cart_product_available_check(instance.product)
