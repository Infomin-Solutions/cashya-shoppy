import random

from . import models
from . import serializers

from django.conf import settings

from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

# Create your views here.


class LogInViewSet(ViewSet):
    serializer_class = serializers.LogInSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            phone_number = data.get('phone_number')
            user, created = models.User.objects.get_or_create(
                phone_number=phone_number)

            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'new_user': created
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshViewSet(ViewSet, TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except TokenError as e:
            raise InvalidToken(e.args[0])


class SendOTP(ViewSet):
    serializer_class = serializers.OTPSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            phone_number = data.get('phone_number')
            # Send OTP to phone_number
            otp = random.randint(1000, 9999)
            models.OTP.objects.create(phone_number=phone_number, otp=otp)

            res = {
                'phone_number': phone_number,
                'success': True,
                'message': 'OTP sent successfully.'
            }
            if settings.DEBUG:
                res['otp'] = otp
            return Response(res, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
