from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def api_root(request):
    return Response({
        'name': 'ResearchGraph AI API',
        'status': 'healthy',
        'version': '1.0.0',
        'endpoints': {
            'ingestion': '/api/ingestion/',
            'retrieval': '/api/retrieval/',
            'claims': '/api/claims/',
            'graph': '/api/graph/',
            'agents': '/api/agents/',
            'evaluation': '/api/evaluation/',
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/health/', api_root, name='api-health'),
    path('api/ingestion/', include('ingestion.urls')),
    path('api/retrieval/', include('retrieval.urls')),
    path('api/claims/', include('claims.urls')),
    path('api/graph/', include('graph.urls')),
    path('api/agents/', include('agents.urls')),
    path('api/evaluation/', include('evaluation.urls')),
]
