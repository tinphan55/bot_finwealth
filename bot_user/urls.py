from django.urls import path
from .views import *

urlpatterns = [
    path('cal_point/', cal_point, name='cal_point'),
    path('api/userinfo/<str:username>/', UserInfoDetailAPIView.as_view(), name='userinfo-detail'),
]