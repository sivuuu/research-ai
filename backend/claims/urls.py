from django.urls import path
from .views import (
    ClaimListView, ClaimDetailView, ClaimReviewView,
    ClaimRelationshipListView, RelationshipReviewView,
    ContradictionQueueView, CrossPaperComparisonMatrixView
)

urlpatterns = [
    path('', ClaimListView.as_view(), name='claim-list'),
    path('<str:pk>/', ClaimDetailView.as_view(), name='claim-detail'),
    path('<str:pk>/review/', ClaimReviewView.as_view(), name='claim-review'),
    path('relationships/list/', ClaimRelationshipListView.as_view(), name='relationship-list'),
    path('relationships/<uuid:pk>/review/', RelationshipReviewView.as_view(), name='relationship-review'),
    path('contradictions/queue/', ContradictionQueueView.as_view(), name='contradiction-queue'),
    path('matrix/compare/', CrossPaperComparisonMatrixView.as_view(), name='comparison-matrix'),
]
