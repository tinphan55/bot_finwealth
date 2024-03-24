from django.contrib import admin

from .models import *

class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('username','total_points', 'email', 'full_name', 'date_of_birth', 'address', 'phone')
    search_fields = ('username', 'email', 'full_name', 'phone')

admin.site.register(UserInfo, UserInfoAdmin)

@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ['user', 'task_points', 'share_points', 'trade_points','promotion_points','used_point', 'total_points']
    list_display_links = ['user']


@admin.register(SharePoint)
class SharePointAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipient', 'points', 'created_at']
    search_fields = ['user__username', 'recipient__username', 'description']
    list_filter = ['created_at']

@admin.register(PromotionPoint)
class PromotionPointAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'created_at']
    search_fields = ['user__username', 'description']
    list_filter = ['created_at']