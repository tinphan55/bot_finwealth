from rest_framework import serializers
from .models import *
from signal_bots.models import *

class FundamentalAnalysisReportSegmentSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='report.date')
    stock = serializers.SerializerMethodField()
    source = serializers.CharField(source='report.source')
    valuation = serializers.FloatField(source='report.valuation')

    def get_stock(self, obj):
        return ', '.join([tag.name for tag in obj.report.tags.all()])

    class Meta:
        model = FundamentalAnalysisReportSegment
        exclude = ['report']

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'

class StockOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockOverview
        exclude = ['id',]

class StockShareholderSerializer(serializers.ModelSerializer):
    ticker = serializers.StringRelatedField()

    class Meta:
        model = StockShareholder
        exclude = ['id',]

class StockOverviewDataTradingSerializer(serializers.ModelSerializer):
    ticker = serializers.StringRelatedField()

    class Meta:
        model = StockOverviewDataTrading
        exclude = ['id',]

class StockValuationSerializer(serializers.ModelSerializer):
    ticker = serializers.StringRelatedField()

    class Meta:
        model = StockValuation
        exclude = ['id',]

class StockRatioDataSerializer(serializers.ModelSerializer):
    ticker = serializers.StringRelatedField()

    class Meta:
        model = StockRatioData
        exclude = ['id',]

class StockPriceFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPriceFilter
        exclude = ['id','date_time',]

class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model= Signal
        fields =  ['ticker','signal','close','take_profit_price','ratio_cutloss','strategy','market_price']

    