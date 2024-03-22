from rest_framework import generics
from .serializers import *
from .models import *
from rest_framework import viewsets

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

class StockPriceFilterAPIViews(generics.ListAPIView):
    serializer_class = StockPriceFilterSerializer
    def get_queryset(self):
        stock = self.kwargs.get('ticker', '')  # Sử dụng kwargs thay vì query_params
        queryset = StockPriceFilter.objects.filter(ticker=stock).order_by('-date')
        return queryset

class StockOverviewDetailAPIView(generics.ListAPIView):
    serializer_class = StockOverviewSerializer
    def get_queryset(self):
        stock = self.kwargs.get('ticker', '')  # Sử dụng kwargs thay vì query_params
        queryset = StockOverview.objects.filter(ticker=stock)
        return queryset
    
class StockShareholderListAPIView(generics.ListAPIView):
    serializer_class = StockShareholderSerializer
    def get_queryset(self):
        stock = self.kwargs.get('ticker', '')  # Sử dụng kwargs thay vì query_params
        queryset = StockShareholder.objects.filter(ticker__ticker=stock)
        return queryset



class StockValuationListAPIView(generics.ListCreateAPIView):
    serializer_class = StockValuationSerializer
    def get_queryset(self):
        stock = self.kwargs.get('ticker', '')  # Sử dụng kwargs thay vì query_params
        queryset = StockValuation.objects.filter(ticker__ticker=stock)
        return queryset

class StockOverviewDataTradingListAPIView(generics.ListAPIView):
    serializer_class = StockOverviewDataTradingSerializer
    def get_queryset(self):
        stock = self.kwargs.get('ticker', '')  # Sử dụng kwargs thay vì query_params
        queryset = StockOverviewDataTrading.objects.filter(ticker__ticker=stock)
        return queryset

class StockRatioDataListAPIView(generics.ListAPIView):
    serializer_class = StockRatioDataSerializer
    def get_queryset(self):
        stock = self.kwargs.get('ticker', '')  # Sử dụng kwargs thay vì query_params
        queryset = StockRatioData.objects.filter(ticker__ticker=stock)
        return queryset
    
class SignalListAPIView(generics.ListAPIView):
    serializer_class = SignalSerializer
    def get_queryset(self):
        queryset = Signal.objects.filter(is_closed=False,is_noti =True)
        return queryset 