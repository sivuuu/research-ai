import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from core.models import ResearchQuery, RetrievedEvidence, ResearchReport, DocumentChunk
from core.serializers import ResearchQuerySerializer, ResearchReportSerializer
from .workflow import MultiAgentResearchWorkflow


class ResearchAgentExecutionView(APIView):
    """Executes the bounded 7-agent LangGraph research synthesis workflow."""

    def post(self, request):
        query_text = request.data.get('query', '').strip()
        if not query_text:
            return Response({'error': 'Query text cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        mode = request.data.get('mode', 'deep_research')
        start_time = time.time()

        # Create Query record
        query_obj = ResearchQuery.objects.create(
            query_text=query_text,
            mode=mode,
            status='RUNNING'
        )

        try:
            workflow = MultiAgentResearchWorkflow()
            result = workflow.execute(query=query_text, mode=mode)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # Persist retrieved evidence
            retrieved_passages = result.get('retrieved_passages', [])
            for p in retrieved_passages:
                chunk_id = p.get('chunk_id')
                if chunk_id:
                    try:
                        chunk = DocumentChunk.objects.get(id=chunk_id)
                        RetrievedEvidence.objects.create(
                            query=query_obj,
                            chunk=chunk,
                            score=p.get('score', 0.0),
                            retrieval_method=p.get('retrieval_method', 'hybrid'),
                            rank=p.get('source_index', 1),
                            subquestion=p.get('subquestion', '')
                        )
                    except DocumentChunk.DoesNotExist:
                        pass

            # Persist report
            rep_data = result.get('final_report', {})
            report_obj = ResearchReport.objects.create(
                query=query_obj,
                title=rep_data.get('title', f"Report: {query_text[:50]}"),
                executive_summary=rep_data.get('executive_summary', ''),
                synthesis_markdown=rep_data.get('synthesis_markdown', ''),
                structured_findings=rep_data.get('structured_findings', []),
                evidence_gaps=rep_data.get('evidence_gaps', []),
                citations=rep_data.get('citations', []),
                faithfulness_score=rep_data.get('faithfulness_score', 1.0),
                metadata={
                    **rep_data.get('metadata', {}),
                    'latency_ms': elapsed_ms,
                    'query_id': str(query_obj.id)
                }
            )

            query_obj.status = 'COMPLETED'
            query_obj.save()

            return Response({
                'query_id': str(query_obj.id),
                'report_id': str(report_obj.id),
                'report': ResearchReportSerializer(report_obj).data,
                'step_history': result.get('step_history', []),
                'subquestions': result.get('subquestions', []),
                'retrieved_passages': retrieved_passages,
                'extracted_claims': result.get('extracted_claims', []),
                'contradictions': result.get('contradictions', []),
                'latency_ms': elapsed_ms
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            query_obj.status = 'FAILED'
            query_obj.save()
            return Response({'error': f"Agent execution failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResearchHistoryView(APIView):
    """Retrieves past research queries and generated reports."""

    def get(self, request):
        queries = ResearchQuery.objects.prefetch_related('reports', 'retrieved_evidence').all().order_by('-created_at')[:20]
        serializer = ResearchQuerySerializer(queries, many=True)
        return Response({
            'count': queries.count(),
            'queries': serializer.data
        })


class ResearchReportExportView(APIView):
    """Exports a research report as Markdown, JSON, or HTML."""

    def get(self, request, pk):
        report = get_object_or_404(ResearchReport, pk=pk)
        fmt = request.query_params.get('format', 'markdown').lower()

        if fmt == 'json':
            return Response(ResearchReportSerializer(report).data)

        if fmt == 'html':
            html_content = f"""<!DOCTYPE html>
<html>
<head>
<title>{report.title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #1e293b; line-height: 1.6; }}
h1, h2, h3 {{ color: #0f172a; }}
.summary {{ background: #f8fafc; border-left: 4px solid #3b82f6; padding: 16px; margin: 20px 0; border-radius: 4px; }}
.citations {{ background: #f1f5f9; padding: 16px; border-radius: 8px; margin-top: 30px; font-size: 0.9em; }}
</style>
</head>
<body>
<h1>{report.title}</h1>
<div class="summary">
<h3>Executive Summary</h3>
<p>{report.executive_summary}</p>
</div>
<div class="content">
<pre style="white-space: pre-wrap; font-family: inherit;">{report.synthesis_markdown}</pre>
</div>
<div class="citations">
<h3>Traceable Citations</h3>
<ul>
{''.join(f"<li><b>[{i+1}]</b> {c.get('document_title')} (p.{c.get('page_number')}): <i>{c.get('source_excerpt')}</i></li>" for i, c in enumerate(report.citations))}
</ul>
</div>
</body>
</html>"""
            response = HttpResponse(html_content, content_type='text/html')
            response['Content-Disposition'] = f'attachment; filename="report_{report.id}.html"'
            return response

        # Default: Markdown
        md_content = f"""# {report.title}

## Executive Summary
{report.executive_summary}

{report.synthesis_markdown}

## Validated Citations & Source Provenance
"""
        for i, c in enumerate(report.citations):
            md_content += f"\n- **[{i+1}]** {c.get('document_title', 'Unknown')} (Page {c.get('page_number', 1)})\n  > \"{c.get('source_excerpt', '')}\"\n"

        response = HttpResponse(md_content, content_type='text/markdown')
        response['Content-Disposition'] = f'attachment; filename="report_{report.id}.md"'
        return response
