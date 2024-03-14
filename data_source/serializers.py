from rest_framework import serializers
from .models import FundamentalAnalysisReport

class FundamentalAnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundamentalAnalysisReport
        exclude = ['file']