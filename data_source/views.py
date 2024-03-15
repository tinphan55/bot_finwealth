from rest_framework import viewsets
from rest_framework.response import Response

from .models import FundamentalAnalysisReport, FundamentalAnalysisReportSegment
from .serializers import FundamentalAnalysisReportSerializer, FundamentalAnalysisReportSegmentSerializer

class FundamentalAnalysisAPIView(viewsets.ViewSet):
    def list(self, request):
        reports = FundamentalAnalysisReport.objects.all()
        segments = FundamentalAnalysisReportSegment.objects.all()

        report_serializer = FundamentalAnalysisReportSerializer(reports, many=True)
        segment_serializer = FundamentalAnalysisReportSegmentSerializer(segments, many=True)

        return Response({
            'reports': report_serializer.data,
            'segments': segment_serializer.data
        })

    def retrieve(self, request, pk=None):
        report = FundamentalAnalysisReport.objects.get(pk=pk)
        
        serializer = FundamentalAnalysisReportSerializer(report)
        return Response(serializer.data)