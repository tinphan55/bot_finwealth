from rest_framework import generics
from .serializers import *
from .models import *

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
        queryset = FundamentalAnalysisReportSegment.objects.filter(report__tags__name=tag).order_by('-report__date')[:100]
        return queryset
    
class NewsListAPIView(generics.ListAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

class NewsDetailAPIView(generics.RetrieveAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer