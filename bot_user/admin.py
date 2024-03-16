from django.contrib import admin

from .models import UserInfo

class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'date_of_birth', 'address', 'phone')
    search_fields = ('username', 'email', 'full_name', 'phone')

admin.site.register(UserInfo, UserInfoAdmin)
