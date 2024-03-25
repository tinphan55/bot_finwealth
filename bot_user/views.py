from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import *
from .serializers import UserInfoSerializer

# class UserInfoListAPIView(generics.ListAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserInfoSerializer

class UserInfoDetailAPIView(generics.ListAPIView):
    serializer_class = UserInfoSerializer
    def get_queryset(self):
        username = self.kwargs.get('username')
        queryset = User.objects.filter(member__total_points__gt=0, username=username)
        return queryset
    
def cal_point(request):
    return render(request, 'bot_user/cal_point.html')