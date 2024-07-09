from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('login', views.LogInViewSet, basename='login')
router.register('refresh', views.TokenRefreshViewSet, basename='refresh')
router.register('send-otp', views.SendOTP, basename='send-otp')
