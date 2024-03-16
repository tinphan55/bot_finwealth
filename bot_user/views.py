from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import UserInfo
from .serializers import UserInfoSerializer

class UserInfoListAPIView(generics.ListAPIView):
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoSerializer

class UserInfoDetailAPIView(generics.RetrieveAPIView):
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoSerializer
    lookup_field = 'username'