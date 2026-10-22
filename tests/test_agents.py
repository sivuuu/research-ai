import pytest
from django.test import TestCase

from core.models import Document, DocumentChunk, IngestionStatus
from agents.workflow import MultiAgentResearchWorkflow
from retrieval.embeddings import EmbeddingEngine


@pytest.mark.django_db
class MultiAgentWorkflowTests(TestCase):

    def setUp(self):
        self.embedder = EmbeddingEngine()
        # Seed an empirical paper
        self.doc = Document.objects.create(
            title="GraphRAG: Unlocking LLM Discovery on Complex Information Networks",
            file_name="graphrag.txt",
            file_hash="hash_wf_01",
            ingestion_status=IngestionStatus.COMPLETED
        )
        self.chunk = DocumentChunk.objects.create(
            document=self.doc,
            chunk_index=0,
            page_number=1,
            section_title="Global Sensemaking",
            text="GraphRAG combines knowledge graph construction with hierarchical summarization to answer global questions across entire corpora.",
            embedding=self.embedder.embed_text("GraphRAG combines knowledge graph construction with hierarchical summarization.")
        )

    def test_multi_agent_execution_and_trace(self):
        workflow = MultiAgentResearchWorkflow()
        result = workflow.execute("How does GraphRAG answer global corpus questions?")

        self.assertEqual(result['status'], 'COMPLETED')
        self.assertTrue(len(result['subquestions']) >= 2)
        self.assertTrue(len(result['retrieved_passages']) >= 1)
        self.assertTrue(len(result['extracted_claims']) >= 1)

        final_rep = result['final_report']
        self.assertIn("GraphRAG", final_rep['title'])
        self.assertTrue(len(final_rep['citations']) >= 1)
        self.assertTrue(final_rep['faithfulness_score'] >= 0.8)

    def test_grounded_refusal_when_evidence_absent(self):
        workflow = MultiAgentResearchWorkflow()
        # Query on completely unindexed, irrelevant topic
        result = workflow.execute("What are the superconducting qubit coherence times in dilution refrigerators?")

        # Since no chunks exist for superconducting qubits, is_sufficient_evidence must be False
        final_rep = result['final_report']
        self.assertIn("Insufficient", final_rep['title'] + final_rep['executive_summary'])
        self.assertTrue(len(final_rep['evidence_gaps']) >= 1)
