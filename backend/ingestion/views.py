import os
import tempfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.shortcuts import get_object_or_404

from core.models import Document, IngestionStatus
from core.serializers import DocumentSerializer, DocumentChunkSerializer
from .pipeline import IngestionPipeline, DuplicateDocumentError


class DocumentListView(APIView):
    """Lists ingested documents and handles document upload."""

    def get(self, request):
        docs = Document.objects.all().order_by('-created_at')
        status_filter = request.query_params.get('status')
        if status_filter:
            docs = docs.filter(ingestion_status=status_filter)
        serializer = DocumentSerializer(docs, many=True)
        return Response({
            'count': docs.count(),
            'documents': serializer.data
        })

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'No file uploaded. Please upload a PDF, TXT, or MD research document.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in settings.ALLOWED_FILE_EXTENSIONS:
            return Response(
                {'error': f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save to media folder or temporary file
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'documents')
        os.makedirs(upload_dir, exist_ok=True)
        safe_path = os.path.join(upload_dir, file_obj.name)

        # Write to disk safely
        with open(safe_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        pipeline = IngestionPipeline()
        try:
            doc = pipeline.process_file(
                file_path=safe_path,
                original_name=file_obj.name
            )
            serializer = DocumentSerializer(doc)
            return Response(
                {'message': 'Document ingested successfully', 'document': serializer.data},
                status=status.HTTP_201_CREATED
            )
        except DuplicateDocumentError as e:
            # Clean up the duplicate file copy
            if os.path.exists(safe_path):
                os.remove(safe_path)
            return Response(
                {'error': str(e), 'existing_doc_id': e.existing_doc_id},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            return Response(
                {'error': f"Ingestion failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentDetailView(APIView):
    """Retrieves or removes a specific document and all its derived records."""

    def get(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        serializer = DocumentSerializer(doc)
        chunks = doc.chunks.all().order_by('chunk_index')
        chunks_data = DocumentChunkSerializer(chunks, many=True).data
        return Response({
            'document': serializer.data,
            'chunks': chunks_data
        })

    def delete(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        file_path = doc.file_path
        # Remove on disk if exists
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        # Cascading delete in Django handles chunks, claims, relationships
        doc_id = str(doc.id)
        doc.delete()
        return Response({
            'message': f"Document {doc_id} and all derived chunks, embeddings, and claims have been permanently deleted."
        }, status=status.HTTP_200_OK)


class DocumentReprocessView(APIView):
    """Re-runs the ingestion pipeline for an existing document."""

    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not os.path.exists(doc.file_path):
            return Response(
                {'error': f"Source file no longer exists at: {doc.file_path}"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Clear existing chunks & claims
        doc.chunks.all().delete()
        doc.claims.all().delete()
        doc.ingestion_status = IngestionStatus.PENDING
        doc.save()

        pipeline = IngestionPipeline()
        try:
            # Temporarily bypass duplicate check for the same document
            pipeline.process_file(doc.file_path, original_name=doc.file_name)
            doc.refresh_from_db()
            return Response(DocumentSerializer(doc).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
