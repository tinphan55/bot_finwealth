

# Create your views here.
from rest_framework import viewsets
from .serializers import FundamentalAnalysisReportSerializer
from .models import FundamentalAnalysisReport

class FundamentalAnalysisReportViewSet(viewsets.ModelViewSet):
    queryset = FundamentalAnalysisReport.objects.all()
    serializer_class = FundamentalAnalysisReportSerializer