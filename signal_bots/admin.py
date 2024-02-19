from django.contrib import admin
from .models import *
from django.urls import reverse
from django.utils.html import format_html

# Register your models here.
class SignalAdmin(admin.ModelAdmin):
    model = Signal
    list_display = ('date','ticker','signal','close','market_price','is_noti','ratio_cutloss','rating_total','rating_fundamental','accumulation', 'is_closed','noted','view_transactions')
    list_filter = ('date','is_closed','noted')
    search_fields =['ticker',]
    def get_search_results(self, request, queryset, search_term):
        # Xử lý khi search_term không trống
        if search_term:
            # Tách các giá trị ticker thành một danh sách
            tickers = search_term.split(',')

            # Sử dụng Q objects để tạo ra điều kiện OR cho mỗi ticker
            q_objects = Q()
            for ticker in tickers:
                q_objects |= Q(ticker__iexact=ticker.strip())

            # Áp dụng điều kiện tìm kiếm
            queryset = queryset.filter(q_objects)
        # Trả về kết quả tìm kiếm
        return queryset, False

    def view_transactions(self, obj):
        url = reverse('admin:manage_bots_overviewbacktest_changelist') + f'?ticker={obj.ticker}'
        return format_html('<a href="{}">Xem kiểm định</a>', url)
    view_transactions.short_description = 'Xem kiểm định'


admin.site.register(Signal, SignalAdmin)