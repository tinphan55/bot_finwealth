from django.urls import path
from .views import *

urlpatterns = [
    path('api/login/', LoginAPIView.as_view(), name='userinfo-detail'),
]