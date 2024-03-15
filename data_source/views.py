from rest_framework import generics
from .serializers import FundamentalAnalysisReportSegmentSerializer
from .models import FundamentalAnalysisReportSegment

class FundamentalAnalysisReportSegmentAPIView(generics.RetrieveAPIView):
    queryset = FundamentalAnalysisReportSegment.objects.all()
    serializer_class = FundamentalAnalysisReportSegmentSerializer



class FundamentalAnalysisReportSegmentListAPIView(generics.ListAPIView):
    queryset = FundamentalAnalysisReportSegment.objects.all()
    serializer_class = FundamentalAnalysisReportSegmentSerializer

class FundamentalAnalysisReportSegmentSearchAPIView(generics.ListAPIView):
    serializer_class = FundamentalAnalysisReportSegmentSerializer

    def get_queryset(self):
        tag = self.request.query_params.get('tag', '')
        queryset = FundamentalAnalysisReportSegment.objects.filter(report__tags__name=tag).order_by('-report_date')[:100]
        return queryset