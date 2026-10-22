import uuid
from django.db import models
from django.conf import settings

# Polyfill or conditional pgvector VectorField
if hasattr(settings, 'DATABASES') and 'postgresql' in settings.DATABASES['default']['ENGINE']:
    try:
        from pgvector.django import VectorField
    except ImportError:
        VectorField = models.JSONField
else:
    VectorField = models.JSONField


class IngestionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PARSING = 'PARSING', 'Parsing'
    EMBEDDING = 'EMBEDDING', 'Embedding'
    EXTRACTING_CLAIMS = 'EXTRACTING_CLAIMS', 'Extracting Claims'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'


class ReviewStatus(models.TextChoices):
    UNREVIEWED = 'UNREVIEWED', 'Unreviewed'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    REJECTED = 'REJECTED', 'Rejected'
    FLAGGED = 'FLAGGED', 'Flagged for Review'


class RelationshipType(models.TextChoices):
    SUPPORTS = 'SUPPORTS', 'Supports'
    CONTRADICTS = 'CONTRADICTS', 'Contradicts'
    QUALIFIES = 'QUALIFIES', 'Qualifies'
    DEPENDS_ON = 'DEPENDS_ON', 'Depends on'
    DERIVED_FROM = 'DERIVED_FROM', 'Derived from'


class RelationshipStatus(models.TextChoices):
    PROPOSED = 'PROPOSED', 'Proposed'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    REJECTED = 'REJECTED', 'Rejected'
    FLAGGED_FOR_HUMAN_REVIEW = 'FLAGGED_FOR_HUMAN_REVIEW', 'Flagged for Human Review'


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=512, default="Untitled Research Document")
    authors = models.JSONField(default=list, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    publication_details = models.CharField(max_length=512, null=True, blank=True)
    abstract = models.TextField(blank=True, default="")
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1024)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    file_size_bytes = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=32, default="pdf")
    total_pages = models.IntegerField(default=1)
    ingestion_status = models.CharField(
        max_length=32,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING,
        db_index=True
    )
    error_message = models.TextField(null=True, blank=True)
    topics = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.file_name})"


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField(default=0)
    page_number = models.IntegerField(default=1)
    section_title = models.CharField(max_length=256, blank=True, default="")
    text = models.TextField()
    start_char = models.IntegerField(default=0)
    end_char = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0)
    embedding = VectorField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'page_number']),
            models.Index(fields=['document', 'chunk_index']),
        ]

    def __str__(self):
        return f"{self.document.title} [p.{self.page_number} c.{self.chunk_index}]"


class Claim(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='claims')
    chunk = models.ForeignKey(DocumentChunk, on_delete=models.SET_NULL, null=True, blank=True, related_name='claims')
    page_number = models.IntegerField(default=1)
    section_title = models.CharField(max_length=256, blank=True, default="")
    claim_text = models.TextField()
    supporting_passage = models.TextField()
    confidence = models.FloatField(default=0.85)
    review_status = models.CharField(
        max_length=32,
        choices=ReviewStatus.choices,
        default=ReviewStatus.UNREVIEWED,
        db_index=True
    )
    entities = models.JSONField(default=list, blank=True)
    topics = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.id}] {self.claim_text[:60]}..."


class ClaimRelationship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='outgoing_relationships')
    target_claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='incoming_relationships')
    relationship_type = models.CharField(
        max_length=32,
        choices=RelationshipType.choices,
        db_index=True
    )
    confidence = models.FloatField(default=0.80)
    evidence_summary = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=32,
        choices=RelationshipStatus.choices,
        default=RelationshipStatus.PROPOSED,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('source_claim', 'target_claim', 'relationship_type')

    def __str__(self):
        return f"{self.source_claim_id} -{self.relationship_type}-> {self.target_claim_id}"


class ReviewDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, null=True, blank=True, related_name='review_decisions')
    relationship = models.ForeignKey(ClaimRelationship, on_delete=models.CASCADE, null=True, blank=True, related_name='review_decisions')
    decision = models.CharField(max_length=32)  # ACCEPT, REJECT, MODIFY
    reviewer_notes = models.TextField(blank=True, default="")
    previous_value = models.JSONField(default=dict, blank=True)
    new_value = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ResearchQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query_text = models.TextField()
    mode = models.CharField(max_length=32, default="deep_research")  # quick_search or deep_research
    filters = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, default="COMPLETED")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.query_text[:50]


class RetrievedEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(ResearchQuery, on_delete=models.CASCADE, related_name='retrieved_evidence', null=True, blank=True)
    chunk = models.ForeignKey(DocumentChunk, on_delete=models.CASCADE, related_name='retrievals')
    score = models.FloatField(default=0.0)
    retrieval_method = models.CharField(max_length=32, default="hybrid")  # vector, lexical, hybrid
    rank = models.IntegerField(default=1)
    subquestion = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rank']


class ResearchReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(ResearchQuery, on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=512)
    executive_summary = models.TextField()
    synthesis_markdown = models.TextField()
    structured_findings = models.JSONField(default=list, blank=True)
    evidence_gaps = models.JSONField(default=list, blank=True)
    citations = models.JSONField(default=list, blank=True)
    faithfulness_score = models.FloatField(default=1.0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class EvaluationRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run_name = models.CharField(max_length=256)
    dataset_name = models.CharField(max_length=256)
    total_questions = models.IntegerField(default=0)
    recall_at_1 = models.FloatField(default=0.0)
    recall_at_3 = models.FloatField(default=0.0)
    recall_at_5 = models.FloatField(default=0.0)
    mrr = models.FloatField(default=0.0)
    citation_precision = models.FloatField(default=0.0)
    citation_coverage = models.FloatField(default=0.0)
    claim_extraction_precision = models.FloatField(default=0.0)
    claim_extraction_recall = models.FloatField(default=0.0)
    contradiction_precision = models.FloatField(default=0.0)
    contradiction_recall = models.FloatField(default=0.0)
    answer_faithfulness = models.FloatField(default=0.0)
    average_latency_ms = models.FloatField(default=0.0)
    metrics_details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.run_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class Entity(models.Model):
    name = models.CharField(max_length=256, unique=True)
    entity_type = models.CharField(max_length=64, default="CONCEPT")
    description = models.TextField(blank=True, default="")
    frequency = models.IntegerField(default=1)
    documents = models.ManyToManyField(Document, related_name='entities', blank=True)

    def __str__(self):
        return f"{self.name} ({self.entity_type})"


class Topic(models.Model):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField(max_length=128, unique=True)
    description = models.TextField(blank=True, default="")
    documents = models.ManyToManyField(Document, related_name='topic_set', blank=True)

    def __str__(self):
        return self.name
