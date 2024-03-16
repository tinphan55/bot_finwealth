from django.urls import path
from .views import *

urlpatterns = [
    path('api/userinfo/', UserInfoListAPIView.as_view(), name='userinfo-list'),
    path('api/userinfo/<str:username>/', UserInfoDetailAPIView.as_view(), name='userinfo-detail'),
]