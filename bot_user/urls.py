from django.urls import path
from .views import UserInfoListAPIView

urlpatterns = [
    path('api/userinfo/', UserInfoListAPIView.as_view(), name='userinfo-list'),
    # ...
]