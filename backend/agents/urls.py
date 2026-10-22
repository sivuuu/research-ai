from django.urls import path
from .views import ResearchAgentExecutionView, ResearchHistoryView, ResearchReportExportView

urlpatterns = [
    path('research/', ResearchAgentExecutionView.as_view(), name='agent-research'),
    path('history/', ResearchHistoryView.as_view(), name='agent-history'),
    path('reports/<uuid:pk>/export/', ResearchReportExportView.as_view(), name='report-export'),
]
