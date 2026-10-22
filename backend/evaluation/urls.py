from django.urls import path
from .views import EvaluationRunListView, EvaluationRunDetailView

urlpatterns = [
    path('runs/', EvaluationRunListView.as_view(), name='evaluation-runs'),
    path('runs/<uuid:pk>/', EvaluationRunDetailView.as_view(), name='evaluation-run-detail'),
]
