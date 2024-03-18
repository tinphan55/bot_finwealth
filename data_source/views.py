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
        start_date = datetime.now().date() - timedelta(days = 365)
        queryset = FundamentalAnalysisReportSegment.objects.filter(report__tags__name=tag, report__date__gte = start_date).order_by('-report__date')
        return queryset
    
class NewsCreateAPIView(generics.CreateAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

class NewsListAPIView(generics.ListAPIView):
    queryset = News.objects.all()
    serializer_class = NewsSerializer