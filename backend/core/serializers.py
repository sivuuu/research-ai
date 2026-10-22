from rest_framework import serializers
from .models import (
    Document, DocumentChunk, Claim, ClaimRelationship,
    ReviewDecision, ResearchQuery, RetrievedEvidence,
    ResearchReport, EvaluationRun, Entity, Topic
)

class DocumentChunkSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'document', 'document_title', 'chunk_index',
            'page_number', 'section_title', 'text', 'start_char',
            'end_char', 'token_count', 'metadata', 'created_at'
        ]


class DocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.IntegerField(source='chunks.count', read_only=True)
    claims_count = serializers.IntegerField(source='claims.count', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'authors', 'publication_date',
            'publication_details', 'abstract', 'file_name',
            'file_hash', 'file_size_bytes', 'file_type',
            'total_pages', 'ingestion_status', 'error_message',
            'topics', 'metadata', 'chunks_count', 'claims_count',
            'created_at', 'updated_at'
        ]


class ClaimRelationshipSerializer(serializers.ModelSerializer):
    source_claim_text = serializers.CharField(source='source_claim.claim_text', read_only=True)
    target_claim_text = serializers.CharField(source='target_claim.claim_text', read_only=True)
    source_doc_title = serializers.CharField(source='source_claim.document.title', read_only=True)
    target_doc_title = serializers.CharField(source='target_claim.document.title', read_only=True)
    source_passage = serializers.CharField(source='source_claim.supporting_passage', read_only=True)
    target_passage = serializers.CharField(source='target_claim.supporting_passage', read_only=True)

    class Meta:
        model = ClaimRelationship
        fields = [
            'id', 'source_claim', 'target_claim', 'relationship_type',
            'confidence', 'evidence_summary', 'status',
            'source_claim_text', 'target_claim_text',
            'source_doc_title', 'target_doc_title',
            'source_passage', 'target_passage',
            'created_at'
        ]


class ClaimSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title', read_only=True)
    file_name = serializers.CharField(source='document.file_name', read_only=True)
    outgoing_relationships = ClaimRelationshipSerializer(many=True, read_only=True)
    incoming_relationships = ClaimRelationshipSerializer(many=True, read_only=True)

    class Meta:
        model = Claim
        fields = [
            'id', 'document', 'document_title', 'file_name',
            'chunk', 'page_number', 'section_title', 'claim_text',
            'supporting_passage', 'confidence', 'review_status',
            'entities', 'topics', 'outgoing_relationships',
            'incoming_relationships', 'created_at'
        ]


class ReviewDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewDecision
        fields = '__all__'


class RetrievedEvidenceSerializer(serializers.ModelSerializer):
    chunk_text = serializers.CharField(source='chunk.text', read_only=True)
    page_number = serializers.IntegerField(source='chunk.page_number', read_only=True)
    section_title = serializers.CharField(source='chunk.section_title', read_only=True)
    doc_id = serializers.UUIDField(source='chunk.document.id', read_only=True)
    doc_title = serializers.CharField(source='chunk.document.title', read_only=True)

    class Meta:
        model = RetrievedEvidence
        fields = [
            'id', 'query', 'chunk', 'chunk_text', 'page_number',
            'section_title', 'doc_id', 'doc_title', 'score',
            'retrieval_method', 'rank', 'subquestion', 'created_at'
        ]


class ResearchReportSerializer(serializers.ModelSerializer):
    query_text = serializers.CharField(source='query.query_text', read_only=True)

    class Meta:
        model = ResearchReport
        fields = [
            'id', 'query', 'query_text', 'title', 'executive_summary',
            'synthesis_markdown', 'structured_findings', 'evidence_gaps',
            'citations', 'faithfulness_score', 'metadata', 'created_at'
        ]


class ResearchQuerySerializer(serializers.ModelSerializer):
    retrieved_evidence = RetrievedEvidenceSerializer(many=True, read_only=True)
    reports = ResearchReportSerializer(many=True, read_only=True)

    class Meta:
        model = ResearchQuery
        fields = [
            'id', 'query_text', 'mode', 'filters',
            'status', 'retrieved_evidence', 'reports', 'created_at'
        ]


class EvaluationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationRun
        fields = '__all__'


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = '__all__'


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'
