from rest_framework import serializers
from .models import *

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['password', 'username', 'first_name', 'last_name']
