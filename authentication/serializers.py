from rest_framework import serializers
from . import models
from django.utils import timezone
from phonenumber_field.phonenumber import PhoneNumber
import requests
from django.conf import settings


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
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                {
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_token
                }
            )
            result = response.json()
        except:
            raise serializers.ValidationError("Recaptcha verification failed")
        if not result.get('success', False):
            raise serializers.ValidationError('Recaptcha verification failed')
        self.recaptcha_verified = True
        return recaptcha_token

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
        # Verify recaptcha token
        try:
            response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                {
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_token
                }
            )
            result = response.json()
        except:
            raise serializers.ValidationError("Recaptcha verification failed")
        if not result.get('success', False):
            raise serializers.ValidationError('Recaptcha verification failed')
        return recaptcha_token
