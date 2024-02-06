from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class BotTelegram (models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name= 'Tên')
    token = models.CharField(max_length=100, verbose_name= 'Token')
    description = models.TextField(max_length=255, blank=True, verbose_name= 'Mô tả')
    owner = models.ForeignKey(User,on_delete=models.CASCADE, verbose_name= 'Chủ bot')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    class Meta:
         verbose_name = 'Bot Telegram'
         verbose_name_plural = 'Bot Telegram'
    def __str__(self):
        return self.name
    
class ChatGroupTelegram (models.Model):
    TYPE_CHOICES = [
        ('internal', 'internal'),
        ('external', 'external'),
    ]
    RANK_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3','3'),
    ]
    name = models.CharField(max_length=50, unique=True, verbose_name= 'Tên')
    token = models.ForeignKey(BotTelegram, on_delete=models.CASCADE,verbose_name= 'Token' )
    chat_id = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=255, blank=True,verbose_name= 'Mô tả')
    type = models.CharField(max_length=20, choices= TYPE_CHOICES, null=False, blank=False,verbose_name= 'Loại')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = 'Ngày tạo' )
    modified_at = models.DateTimeField(auto_now=True, verbose_name = 'Ngày chỉnh sửa' )
    rank  = models.CharField(max_length=20, choices= RANK_CHOICES, null=False, blank=False, verbose_name= 'Cấp')
    is_signal = models.BooleanField(default=True,verbose_name= 'Gửi tín hiệu')
    class Meta:
         verbose_name = 'Nhóm Telegram'
         verbose_name_plural = 'Nhóm Telegram'
    
    def __str__(self):
        return self.name