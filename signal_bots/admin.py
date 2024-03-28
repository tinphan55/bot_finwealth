from django.contrib import admin
from .models import *
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Q

# Register your models here.
class SignalAdmin(admin.ModelAdmin):
    model = Signal
    list_display = ('date','ticker','signal','close','market_price','is_noti','ratio_cutloss','rating_total','rating_fundamental','accumulation', 'is_closed','noted','view_transactions')
    list_filter = ('date','is_closed','noted')
    search_fields =['ticker',]


    def view_transactions(self, obj):
        url = reverse('admin:manage_bots_overviewbacktest_changelist') + f'?ticker={obj.ticker}'
        return format_html('<a href="{}">Xem kiểm định</a>', url)
    view_transactions.short_description = 'Xem kiểm định'


admin.site.register(Signal, SignalAdmin)