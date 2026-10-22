from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .search import HybridRetriever
from .reranker import Reranker
from .validator import CitationValidator


class SearchView(APIView):
    """Executes semantic, lexical, or hybrid retrieval with optional reranking."""

    def post(self, request):
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query string cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        top_k = int(request.data.get('top_k', 6))
        method = request.data.get('method', 'hybrid')
        filters = request.data.get('filters', {})
        rerank = bool(request.data.get('rerank', False))
        min_score = float(request.data.get('min_score', 0.10))

        retriever = HybridRetriever()
        results = retriever.search(
            query=query,
            top_k=top_k if not rerank else top_k * 2,
            method=method,
            filters=filters,
            min_score=min_score
        )

        if rerank and results:
            results = Reranker.rerank(query, results, top_k=top_k)

        return Response({
            'query': query,
            'method': method,
            'reranked': rerank,
            'total_retrieved': len(results),
            'results': results
        })


class CitationValidationView(APIView):
    """Validates citations in a synthesis text against retrieved evidence."""

    def post(self, request):
        text = request.data.get('text', '')
        retrieved_chunks = request.data.get('retrieved_chunks', [])

        validation = CitationValidator.validate_report(text, retrieved_chunks)
        return Response(validation)
