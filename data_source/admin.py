from django.contrib import admin
from .models import *
from bot_user.models import Member
from django.utils.html import format_html

# Register your models here.

class FundamentalAnalysisReportSegmentAdmin(admin.TabularInline):
    model = FundamentalAnalysisReportSegment
    fields = ('segment','len_text')
    readonly_fields = ['len_text',]
    def len_text(self,obj):
        if obj.segment:
            return len(obj.segment)
    
class FundamentalAnalysisReportAdmin(admin.ModelAdmin):
    model = FundamentalAnalysisReport
    inlines = [FundamentalAnalysisReportSegmentAdmin]
    list_display = ['image_tag','username','name','date', 'source', 'valuation','get_report_tags','modified_date']
    list_display_links =['name',]
    readonly_fields = ['username',]
    fieldsets = (
        ('Thông tin báo cáo', {
            'fields': ('date', 'tags', 'file', 'source', 'valuation')
        }),
    )
    search_fields = ['tags__name',]
    list_filter = ['username',]

    def get_report_tags(self, obj):
        return ", ".join([str(tag) for tag in obj.tags.all()])  # Đổi obj.tags thành obj.tags.all()
    get_report_tags.short_description = 'Tags'  # Điều này sẽ hiển thị 'Tags' như tiêu đề của cột

    def image_tag(self, obj):
        member = Member.objects.filter(id_member__username =obj.username).first()
        if member is not None and member.avatar:
            return format_html('<img src="{}" style="border-radius: 50%; width: 40px; height: 40px; object-fit: cover;"/>'.format(member.avatar.url))
        else:
            return format_html('<img src="/static/bot_user/img/default-img.jpg"style="border-radius: 50%; width: 40px; height: 40px; object-fit: cover;"/>')                   

    image_tag.short_description = 'Người chia sẽ'

    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        obj.username = request.user.username
        obj.save()

# class StockFundamentalDataAdmin(admin.ModelAdmin):
#     model= StockFundamentalData
#     list_display = ['ticker','p_e','p_b','roa','roe','dept_ratio','growth_rating','stable_rating','valuation_rating','fundamental_rating']
#     search_fields = ['ticker',]
#     inlines=[FundamentalAnalysisAdmin,]

admin.site.register(FundamentalAnalysisReport,FundamentalAnalysisReportAdmin)
admin.site.register(Tag)

class NewsAdmin(admin.ModelAdmin):
    list_display = ['image_tag','username', 'source', 'modified_date', 'tags','content',]
    readonly_fields =['username',]
    search_fields = ['username', 'source', 'tags']
    # list_editable = ['content',]
    list_filter = ['username',]
    def save_model(self, request, obj, form, change):
        # Lưu người dùng đang đăng nhập vào trường user nếu đang tạo cart mới
        if obj.username is None:
            obj.username = request.user.username
            obj.save()
    def image_tag(self, obj):
        member = Member.objects.filter(id_member__username =obj.username).first()
        if member is not None and member.avatar:
            return format_html('<img src="{}" style="border-radius: 50%; width: 40px; height: 40px; object-fit: cover;"/>'.format(member.avatar.url))
        else:
            return format_html('<img src="/static/bot_user/img/default-img.jpg"style="border-radius: 50%; width: 40px; height: 40px; object-fit: cover;"/>')                   

    image_tag.short_description = 'Người chia sẽ'
    
admin.site.register(News,NewsAdmin)


@admin.register(StockOverview)
class StockOverviewAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'company_name', 'stock_exchange','listed_date')
    search_fields =('ticker',)

@admin.register(StockShareholder)
class StockShareholderAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'shareholder_name', 'role_type', 'number_of_shares', 'ownership_pct', 'effective_date')
    search_fields =('ticker__ticker',)
@admin.register(StockValuation)
class StockValuationAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'firm', 'report_date', 'source', 'report_price', 'target_price')
    search_fields =('ticker__ticker',)

class StockOverviewDataTradingAdmin(admin.ModelAdmin):
    list_display = ('ticker','price', 'marketcap', 'volume_avg_cr_10d', 'price_highest_cr_52w', 'price_lowest_cr_52w', 'outstanding_shares', 'freefloat', 'beta', 'price_to_earnings', 'price_to_book', 'dividend_yield', 'bvps_cr', 'roae_tr_avg5q', 'roaa_tr_avg5q', 'eps_tr', 'avg_target_price')
    search_fields =('ticker__ticker',)
admin.site.register(StockOverviewDataTrading, StockOverviewDataTradingAdmin)

class StockRatioDataAdmin(admin.ModelAdmin):
       list_display = ('ticker','report_date', 'item_name', 'value')
   
admin.site.register(StockRatioData, StockRatioDataAdmin)


