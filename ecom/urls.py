from . import views
from django.urls import path

urlpatterns = [
    path(
        'callback', views.payment_callback, name='payment-callback'),
]
