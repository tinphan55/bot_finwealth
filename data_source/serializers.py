from rest_framework import serializers
from .models import FundamentalAnalysisReportSegment, FundamentalAnalysisReport

class FundamentalAnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundamentalAnalysisReport
        fields = '__all__'

class FundamentalAnalysisReportSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundamentalAnalysisReportSegment
        fields = '__all__'