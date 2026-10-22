import pytest
from django.test import TestCase

from core.models import Document, DocumentChunk, Claim, ClaimRelationship, RelationshipType, ReviewStatus
from claims.extractor import ClaimExtractor
from claims.comparator import EvidenceComparator


@pytest.mark.django_db
class ClaimAndEvidenceTests(TestCase):

    def setUp(self):
        self.docA = Document.objects.create(
            title="Analysis of RAG Latency",
            file_name="rag_latency.txt",
            file_hash="hash_a1"
        )
        self.docB = Document.objects.create(
            title="Scalability of Knowledge Graphs",
            file_name="kg_scale.txt",
            file_hash="hash_b1"
        )

        self.claim1 = Claim.objects.create(
            id="CLM-TEST-01",
            document=self.docA,
            page_number=2,
            section_title="Latency",
            claim_text="Dense vector retrieval significantly improves query throughput and minimizes latency across billion-scale corpora.",
            supporting_passage="In our experiments, dense vector retrieval significantly improves query throughput and minimizes latency across billion-scale corpora.",
            confidence=0.92,
            entities=["Dense Retrieval", "Latency"]
        )

        self.claim2 = Claim.objects.create(
            id="CLM-TEST-02",
            document=self.docB,
            page_number=5,
            section_title="Trade-offs",
            claim_text="Dense vector retrieval severely degrades query throughput and fails to scale on large corpora without indexing.",
            supporting_passage="Our results demonstrate that dense vector retrieval severely degrades query throughput and fails to scale on large corpora without indexing.",
            confidence=0.88,
            entities=["Dense Retrieval", "Latency"]
        )

    def test_contradiction_detection(self):
        rel = EvidenceComparator.compare_claims(self.claim1, self.claim2)
        self.assertIsNotNone(rel)
        self.assertEqual(rel['relationship_type'], RelationshipType.CONTRADICTS)
        self.assertTrue(rel['confidence'] > 0.70)
        self.assertIn("Contradictory findings", rel['evidence_summary'])

    def test_support_detection(self):
        claim_support = Claim.objects.create(
            id="CLM-TEST-03",
            document=self.docB,
            page_number=1,
            claim_text="Dense vector retrieval significantly improves search accuracy and enhances factual recall.",
            supporting_passage="Dense vector retrieval significantly improves search accuracy and enhances factual recall.",
            confidence=0.90,
            entities=["Dense Retrieval"]
        )
        rel = EvidenceComparator.compare_claims(self.claim1, claim_support)
        self.assertIsNotNone(rel)
        self.assertEqual(rel['relationship_type'], RelationshipType.SUPPORTS)

    def test_claim_review_lifecycle(self):
        self.assertEqual(self.claim1.review_status, ReviewStatus.UNREVIEWED)
        self.claim1.review_status = ReviewStatus.ACCEPTED
        self.claim1.save()

        updated = Claim.objects.get(id="CLM-TEST-01")
        self.assertEqual(updated.review_status, ReviewStatus.ACCEPTED)
