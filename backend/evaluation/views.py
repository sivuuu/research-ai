from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import EvaluationRun
from core.serializers import EvaluationRunSerializer
from .runner import EvaluationRunner


class EvaluationRunListView(APIView):
    """Lists past evaluation runs and triggers new benchmark runs."""

    def get(self, request):
        runs = EvaluationRun.objects.all().order_by('-created_at')[:25]
        serializer = EvaluationRunSerializer(runs, many=True)
        return Response({
            'count': runs.count(),
            'runs': serializer.data
        })

    def post(self, request):
        run_name = request.data.get('run_name')
        dataset_path = request.data.get('dataset_path')

        runner = EvaluationRunner(dataset_path=dataset_path)
        try:
            results = runner.run_benchmark(run_name=run_name)
            return Response(results, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f"Evaluation run failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EvaluationRunDetailView(APIView):
    """Retrieves detailed per-query diagnostic logs for a specific evaluation run."""

    def get(self, request, pk):
        run = get_object_or_404(EvaluationRun, pk=pk)
        return Response(EvaluationRunSerializer(run).data)
