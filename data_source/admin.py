from django.contrib import admin
from .models import *

# Register your models here.
class FundamentalAnalysisAdmin(admin.StackedInline):
    model = FundamentalAnalysis

class StockFundamentalDataAdmin(admin.ModelAdmin):
    model= StockFundamentalData
    list_display = ['ticker','p_e','p_b','roa','roe','dept_ratio','growth_rating','stable_rating','valuation_rating','fundamental_rating']
    search_fields = ['ticker',]
    inlines=[FundamentalAnalysisAdmin,]

admin.site.register(StockFundamentalData,StockFundamentalDataAdmin)