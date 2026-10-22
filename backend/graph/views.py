from rest_framework.views import APIView
from rest_framework.response import Response
from .service import GraphService


class KnowledgeGraphView(APIView):
    """Returns the interconnected evidence graph for visualization and query."""

    def get(self, request):
        doc_id = request.query_params.get('document_id')
        topic = request.query_params.get('topic')
        include_evidence = request.query_params.get('include_evidence', 'true').lower() == 'true'

        graph_data = GraphService.get_graph(
            document_id=doc_id,
            topic=topic,
            include_evidence_nodes=include_evidence
        )
        return Response(graph_data)
