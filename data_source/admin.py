from django.contrib import admin
from .models import *

# Register your models here.

class FundamentalAnalysisReportSegmentAdmin(admin.TabularInline):
    model = FundamentalAnalysisReportSegment
    fields = ('segment',)
    readonly_fields = ['segment',]
class FundamentalAnalysisReportAdmin(admin.ModelAdmin):
    model = FundamentalAnalysisReport
    inlines = [FundamentalAnalysisReportSegmentAdmin]
    fieldsets = (
        ('Thông tin báo cáo', {
            'fields': ('date', 'tags', 'file', 'source', 'valuation')
        }),
    )

# class StockFundamentalDataAdmin(admin.ModelAdmin):
#     model= StockFundamentalData
#     list_display = ['ticker','p_e','p_b','roa','roe','dept_ratio','growth_rating','stable_rating','valuation_rating','fundamental_rating']
#     search_fields = ['ticker',]
#     inlines=[FundamentalAnalysisAdmin,]

admin.site.register(FundamentalAnalysisReport,FundamentalAnalysisReportAdmin)
admin.site.register(Tag)