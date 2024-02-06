from django.contrib import admin
from .models import *

# Register your models here.
class ChatGroupTelegramAdmin(admin.StackedInline):
    model = ChatGroupTelegram



class BotTelegramAdmin(admin.ModelAdmin):
    inlines = [ChatGroupTelegramAdmin,]
    model = BotTelegram
    
admin.site.register(BotTelegram,BotTelegramAdmin)