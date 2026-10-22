from django.urls import path
from .views import KnowledgeGraphView

urlpatterns = [
    path('data/', KnowledgeGraphView.as_view(), name='graph-data'),
]
