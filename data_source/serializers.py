from rest_framework import serializers
from .models import *

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