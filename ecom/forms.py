from . import models
from django import forms


class OrderStatusInlineForm(forms.ModelForm):
    class Meta:
        model = models.OrderStatus
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        order_instance = self.instance.order if self.instance.pk else None
        if order_instance:
            self.base_fields['status'].widget.choices = order_instance.get_status_choices(
            )[1:]
            self.fields['status'].widget.choices = order_instance.get_status_choices(
                self.instance.status)
