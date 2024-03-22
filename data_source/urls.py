from django.urls import path
from .views import *

urlpatterns = [
    # Các url hiện có trong ứng dụng của bạn
    # ...
    path('api/report_segment/', FundamentalAnalysisReportSegmentListAPIView.as_view(), name='segment-list-api'),
    path('api/report_segment/<int:pk>/', FundamentalAnalysisReportSegmentAPIView.as_view(), name='segment-api'),
    path('api/segment/search/', FundamentalAnalysisReportSegmentSearchAPIView.as_view(), name='segment-search-api'),
    path('api/news/create/', NewsCreateAPIView.as_view(), name='news-create'),
    path('api/news/list/', NewsListAPIView.as_view(), name='news-list'),
    path('api/stock-overview/<str:ticker>/', StockOverviewDetailAPIView.as_view(), name='stock_overview_detail'),
    path('api/stock-shareholder/<str:ticker>/', StockShareholderListAPIView.as_view(), name='stock_shareholder_list'),
    path('api/stock-valuation/<str:ticker>/', StockValuationListAPIView.as_view(), name='stock_valuation_list'),
    path('api/stock-data-trading/<str:ticker>/', StockOverviewDataTradingListAPIView.as_view(), name='stock_data_trading'),
    path('api/stock-ratio-data/<str:ticker>/', StockRatioDataListAPIView.as_view(), name='stock_ratio_data'),
    path('api/stockprice/<str:ticker>/', StockPriceFilterAPIViews.as_view(),name='stock_price'),
    path('api/signal/', SignalListAPIView.as_view(),name='signal'),

]   