from django.shortcuts import render

# Create your views here.
from .models import *
from .serializers import UserSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# class UserInfoListAPIView(generics.ListAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserInfoSerializer

class LoginAPIView(generics.CreateAPIView):
    serializer_class = UserSerializer
    """
    API endpoint để đăng nhập và nhận thông tin người dùng
    """
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        # Xác thực thông tin đăng nhập
        user = authenticate(username=username, password=password)
        if user is not None:
            last_name = user.last_name
            point = user.member.total_points
            # Nếu thông tin đăng nhập hợp lệ, trả về thông tin người dùng từ API UserInfoDetailAPIView
            return Response({"last_name": last_name,
                             "point":point})  # Trả về dưới dạng JSON
        else:
            return Response({"error": "Tên người dùng hoặc mật khẩu không chính xác."}, status=status.HTTP_401_UNAUTHORIZED)
def cal_point(request):
    return render(request, 'bot_user/cal_point.html')


