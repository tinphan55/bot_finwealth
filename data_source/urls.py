from django.urls import path
from .views import FundamentalAnalysisAPIView

urlpatterns = [
    path('api/fundamental-analysis/', FundamentalAnalysisAPIView.as_view({'get': 'list'}), name='fundamental_analysis_api'),
    path('api/fundamental-analysis/<int:pk>/', FundamentalAnalysisAPIView.as_view({'get': 'retrieve'}), name='fundamental_analysis_detail_api'),
]