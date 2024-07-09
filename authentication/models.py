from django.db import models
from .managers import UserManager
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.


class User(AbstractUser):
    username = None
    email = models.EmailField(
        "Email Address",
        unique=True,
        blank=True,
        null=True
    )
    phone_number = PhoneNumberField(blank=False, unique=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone_number.as_e164


class OTP(models.Model):
    phone_number = models.EmailField(max_length=254)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.phone_number) + ' - ' + self.otp
