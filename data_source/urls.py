from django.urls import path
from .views import *

urlpatterns = [
    # Các url hiện có trong ứng dụng của bạn
    # ...
    path('api/report_segment/', FundamentalAnalysisReportSegmentListAPIView.as_view(), name='segment-list-api'),
    path('api/report_segment/<int:pk>/', FundamentalAnalysisReportSegmentAPIView.as_view(), name='segment-api'),
    path('api/segment/search/', FundamentalAnalysisReportSegmentSearchAPIView.as_view(), name='segment-search-api'),
    path('api/news/', NewsListAPIView.as_view(), name='news-list'),
    path('api/news/<int:pk>/', NewsDetailAPIView.as_view(), name='news-detail'),
]