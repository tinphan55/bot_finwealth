from rest_framework import serializers
from .models import FundamentalAnalysisReportSegment, FundamentalAnalysisReport

class FundamentalAnalysisReportSegmentSerializer(serializers.ModelSerializer):
    report_date = serializers.DateField(source='report.date')
    report_tags = serializers.SerializerMethodField()
    report_source = serializers.CharField(source='report.source')
    report_valuation = serializers.FloatField(source='report.valuation')

    def get_report_tags(self, obj):
        return ', '.join([tag.name for tag in obj.report.tags.all()])

    class Meta:
        model = FundamentalAnalysisReportSegment
        exclude = ['report']

