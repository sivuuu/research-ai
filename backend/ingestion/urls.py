from django.urls import path
from .views import DocumentListView, DocumentDetailView, DocumentReprocessView

urlpatterns = [
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('upload/', DocumentListView.as_view(), name='document-upload'),
    path('documents/<uuid:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<uuid:pk>/reprocess/', DocumentReprocessView.as_view(), name='document-reprocess'),
]
