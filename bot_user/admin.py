from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import *
from django.db.models import Q

class MemberInline(admin.StackedInline):
    model = Member
    verbose_name_plural = 'member'
    can_delete = False
    #search_fields = ["firstname", "lastname"]
    fields = ['avatar','phone','total_points' ]
    readonly_fields =['total_points']

class CustomUserAdmin(UserAdmin):
    inlines = (MemberInline, )
    list_display = ["image_tag","username","first_name", "last_name", 'last_login',"is_active"]
    list_display_links = ["username",]

    def image_tag(self, obj):
        member = Member.objects.filter(id_member_id =obj.id).first()
        if member is not None and member.avatar:
            return format_html('<img src="{}" style="border-radius: 50%; width: 40px; height: 40px; object-fit: cover;"/>'.format(member.avatar.url))
        else:
            return format_html('<img src="/media/member/default-image.jpg"style="border-radius: 50%; width: 40px; height: 40px; object-fit: cover;"/>')                   

    image_tag.short_description = 'avatar'


    def total_points(self, obj):
        member = Member.objects.filter(id_member_id =obj.id).first()
        if member is not None:
            return member.total_points
    total_points.short_description = 'Tổng điểm'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ['user', 'task_points', 'share_points','promotion_points','used_point', 'total_points']
    list_display_links = ['user']
    search_fields = ['user__id_member__username',]
    def get_queryset(self, request):
        if not request.user.is_superuser:
            # Chỉ trả về các bản ghi có sum_stock > 0
            return super().get_queryset(request).filter(user__id_member__username=request.user.username)
        else:
            return super().get_queryset(request).all()



@admin.register(SharePoint)
class SharePointAdmin(admin.ModelAdmin):
    list_display = ['user','recipient', 'points', 'created_at']
    search_fields = ['user__id_member__username', 'recipient__id_member__username', ]
    list_filter = ['created_at']
    fields =['recipient', 'points','description']
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if obj.user is None:
            obj.user = request.user.member
            obj.save()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "recipient":
            # Loại bỏ request.user khỏi danh sách lựa chọn
            kwargs["queryset"] = db_field.remote_field.model.objects.exclude(id_member__username=request.user.username)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        if not request.user.is_superuser:
            # Chỉ trả về các bản ghi có sum_stock > 0
            return super().get_queryset(request).filter(Q(user__id_member__username=request.user.username) | Q(recipient__id_member__username=request.user.username))
        else:
            return super().get_queryset(request).all()
        
@admin.register(PromotionPoint)
class PromotionPointAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'created_at']
    search_fields = ['user__id_member__username', ]
    list_filter = ['created_at']

    def get_queryset(self, request):
        if not request.user.is_superuser:
            # Chỉ trả về các bản ghi có sum_stock > 0
            return super().get_queryset(request).filter(user__id_member__username=request.user.username)
        else:
            return super().get_queryset(request).all()