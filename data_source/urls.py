from django.urls import include, path
from rest_framework import routers
from .views import FundamentalAnalysisReportViewSet

router = routers.DefaultRouter()
router.register(r'fundamental-analysis-reports', FundamentalAnalysisReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]