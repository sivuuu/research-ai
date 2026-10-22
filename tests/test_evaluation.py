import pytest
from django.test import TestCase

from evaluation.metrics import EvaluationMetrics
from evaluation.runner import EvaluationRunner
from core.models import EvaluationRun, Document, DocumentChunk, IngestionStatus
from retrieval.embeddings import EmbeddingEngine


@pytest.mark.django_db
class EvaluationFrameworkTests(TestCase):

    def setUp(self):
        self.embedder = EmbeddingEngine()
        # Seed test documents required for benchmark evaluation
        self.doc1 = Document.objects.create(
            title="GraphRAG: Unlocking LLM Discovery on Complex Information Networks",
            file_name="graphrag.txt",
            file_hash="eval_hash_01",
            ingestion_status=IngestionStatus.COMPLETED
        )
        self.chunk1 = DocumentChunk.objects.create(
            document=self.doc1,
            chunk_index=0,
            page_number=1,
            section_title="Global Sensemaking",
            text="GraphRAG combines knowledge graph construction with hierarchical community summarization to answer global sensemaking questions.",
            embedding=self.embedder.embed_text("GraphRAG combines knowledge graph construction with hierarchical community summarization.")
        )

    def test_recall_at_k(self):
        retrieved = ["chunk_1", "chunk_2", "chunk_3", "chunk_4", "chunk_5"]
        expected = ["chunk_2", "chunk_5"]

        r1 = EvaluationMetrics.recall_at_k(retrieved, expected, k=1)
        r3 = EvaluationMetrics.recall_at_k(retrieved, expected, k=3)
        r5 = EvaluationMetrics.recall_at_k(retrieved, expected, k=5)

        self.assertEqual(r1, 0.0)
        self.assertEqual(r3, 0.5)  # chunk_2 is in top 3
        self.assertEqual(r5, 1.0)  # chunk_2 and chunk_5 are in top 5

    def test_reciprocal_rank(self):
        retrieved = ["chunk_a", "chunk_b", "chunk_target"]
        expected = ["chunk_target"]
        mrr = EvaluationMetrics.reciprocal_rank(retrieved, expected)
        self.assertAlmostEqual(mrr, 1.0 / 3.0, places=4)

    def test_claim_extraction_f1(self):
        extracted = [
            "GraphRAG combines knowledge graph construction with community summarization",
            "Vector search is inadequate for global queries"
        ]
        labeled = [
            "GraphRAG combines knowledge graph construction with hierarchical summarization",
            "Vector search fails on global sensemaking"
        ]
        p, r, f1 = EvaluationMetrics.claim_extraction_precision_recall(extracted, labeled, match_threshold=0.3)
        self.assertTrue(f1 >= 0.8)

    def test_contradiction_f1(self):
        detected = [("claim_alpha", "claim_beta")]
        labeled = [("claim_alpha", "claim_beta")]
        p, r, f1 = EvaluationMetrics.contradiction_detection_precision_recall(detected, labeled)
        self.assertEqual(p, 1.0)
        self.assertEqual(r, 1.0)
        self.assertEqual(f1, 1.0)

    def test_evaluation_runner_execution(self):
        runner = EvaluationRunner()
        result = runner.run_benchmark(run_name="Test-Pytest-Run")

        self.assertIn("summary", result)
        self.assertTrue(result['total_questions'] >= 5)
        self.assertTrue(EvaluationRun.objects.filter(run_name="Test-Pytest-Run").exists())
