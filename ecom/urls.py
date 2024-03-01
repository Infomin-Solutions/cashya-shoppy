from . import views
from django.urls import path, include

urlpatterns = [
    path('api/', include('ecom.urls_api')),
]
