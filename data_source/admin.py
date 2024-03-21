from django.contrib import admin
from .models import *

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
    list_display = ['name','date', 'source', 'valuation','get_report_tags']
    fieldsets = (
        ('Thông tin báo cáo', {
            'fields': ('date', 'tags', 'file', 'source', 'valuation')
        }),
    )
    def get_report_tags(self, obj):
        return ", ".join([str(tag) for tag in obj.tags.all()])  # Đổi obj.tags thành obj.tags.all()
    get_report_tags.short_description = 'Tags'  # Điều này sẽ hiển thị 'Tags' như tiêu đề của cột

# class StockFundamentalDataAdmin(admin.ModelAdmin):
#     model= StockFundamentalData
#     list_display = ['ticker','p_e','p_b','roa','roe','dept_ratio','growth_rating','stable_rating','valuation_rating','fundamental_rating']
#     search_fields = ['ticker',]
#     inlines=[FundamentalAnalysisAdmin,]

admin.site.register(FundamentalAnalysisReport,FundamentalAnalysisReportAdmin)
admin.site.register(Tag)
admin.site.register(News)


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