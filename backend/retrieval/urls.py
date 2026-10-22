from django.urls import path
from .views import SearchView, CitationValidationView

urlpatterns = [
    path('search/', SearchView.as_view(), name='retrieval-search'),
    path('validate-citations/', CitationValidationView.as_view(), name='citation-validate'),
]
