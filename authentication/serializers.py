from rest_framework import serializers
from . import models
from django.utils import timezone
from phonenumber_field.phonenumber import PhoneNumber
from .utils import recaptcha_verify


class LogInSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    recaptcha_token = serializers.CharField(required=True)
    otp = serializers.CharField(required=True)

    def validate_phone_number(self, phone_number):
        phone_number = PhoneNumber.from_string(phone_number)
        if phone_number.is_valid():
            return phone_number.as_e164
        raise serializers.ValidationError("Invalid phone number")

    def validate_recaptcha_token(self, recaptcha_token):
        if recaptcha_verify(recaptcha_token):
            self.recaptcha_verified = True
            return recaptcha_token
        raise serializers.ValidationError("Recaptcha verification failed")

    def validate_otp(self, otp):
        if not getattr(self, 'recaptcha_verified', False):
            return otp

        now = timezone.now()
        phone_number = PhoneNumber.from_string(
            self.initial_data.get('phone_number'))
        query = models.OTP.objects.filter(
            phone_number=phone_number, otp=otp, created_at__gte=now - timezone.timedelta(minutes=5))
        if not query.exists():
            raise serializers.ValidationError("Invalid OTP")
        query.delete()
        return otp


class OTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    recaptcha_token = serializers.CharField(required=True)

    def validate_phone_number(self, phone_number):
        phone_number = PhoneNumber.from_string(phone_number)
        if phone_number.is_valid():
            return phone_number.as_e164
        raise serializers.ValidationError("Invalid phone number")

    def validate_recaptcha_token(self, recaptcha_token):
        if recaptcha_verify(recaptcha_token):
            return recaptcha_token
        raise serializers.ValidationError("Recaptcha verification failed")
