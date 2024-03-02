
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from . import models


def order_status_change(sender, instance: models.OrderStatus, **kwargs):
    order = instance.order
    status = order.get_status_choices()[0][1]
    order.status = status
    order.save()


@receiver(post_save, sender=models.OrderStatus)
def order_status_post_save(sender, instance: models.OrderStatus, **kwargs):
    order_status_change(sender, instance, **kwargs)


@receiver(post_delete, sender=models.OrderStatus)
def order_status_post_delete(sender, instance: models.OrderStatus, **kwargs):
    order_status_change(sender, instance, **kwargs)
