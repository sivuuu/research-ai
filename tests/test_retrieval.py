import pytest
from django.test import TestCase

from core.models import Document, DocumentChunk, IngestionStatus
from retrieval.search import HybridRetriever
from retrieval.validator import CitationValidator
from retrieval.embeddings import EmbeddingEngine


@pytest.mark.django_db
class RetrievalAndCitationTests(TestCase):

    def setUp(self):
        self.retriever = HybridRetriever()
        self.embedder = EmbeddingEngine()

        # Seed test documents and chunks
        self.doc1 = Document.objects.create(
            title="Graph Neural Networks for Knowledge Reasoning",
            file_name="gnn_reasoning.txt",
            file_hash="hash_gnn_001",
            ingestion_status=IngestionStatus.COMPLETED
        )
        self.chunk1 = DocumentChunk.objects.create(
            document=self.doc1,
            chunk_index=0,
            page_number=1,
            section_title="Architecture",
            text="Graph neural networks propagate node embeddings across multi-hop relational paths to reason over sparse knowledge graphs.",
            start_char=0,
            end_char=120,
            token_count=18,
            embedding=self.embedder.embed_text("Graph neural networks propagate node embeddings across multi-hop relational paths.")
        )

        self.doc2 = Document.objects.create(
            title="Fast Approximate Nearest Neighbor Search",
            file_name="ann_search.txt",
            file_hash="hash_ann_002",
            ingestion_status=IngestionStatus.COMPLETED
        )
        self.chunk2 = DocumentChunk.objects.create(
            document=self.doc2,
            chunk_index=0,
            page_number=3,
            section_title="Benchmarks",
            text="HNSW indexes provide sub-10ms approximate nearest neighbor query latency on dense billion-scale vector collections.",
            start_char=0,
            end_char=110,
            token_count=15,
            embedding=self.embedder.embed_text("HNSW indexes provide sub-10ms approximate nearest neighbor query latency on dense billion-scale vector collections.")
        )

    def test_vector_and_lexical_retrieval(self):
        results = self.retriever.search("multi-hop relational graph neural networks", top_k=2, method="hybrid")
        self.assertTrue(len(results) > 0)
        top_match = results[0]
        self.assertEqual(top_match['document_id'], str(self.doc1.id))
        self.assertEqual(top_match['page_number'], 1)

    def test_metadata_filtering(self):
        # Filter strictly for doc2
        results = self.retriever.search(
            "neural networks",
            top_k=5,
            filters={'document_ids': [str(self.doc2.id)]}
        )
        self.assertTrue(all(r['document_id'] == str(self.doc2.id) for r in results))

    def test_citation_validator_valid_and_hallucinated(self):
        retrieved_chunks = [
            {
                'chunk_id': str(self.chunk1.id),
                'document_id': str(self.doc1.id),
                'document_title': self.doc1.title,
                'page_number': 1,
                'section_title': "Architecture",
                'text': self.chunk1.text
            }
        ]

        # Valid citation [1]
        valid_synthesis = "GNNs propagate embeddings across multi-hop paths to reason over graphs [1]."
        res_valid = CitationValidator.validate_report(valid_synthesis, retrieved_chunks)
        self.assertEqual(res_valid['total_citations'], 1)
        self.assertEqual(res_valid['valid_citations_count'], 1)
        self.assertEqual(res_valid['hallucinated_citations_count'], 0)
        self.assertEqual(res_valid['citation_precision'], 1.0)

        # Hallucinated citation [99]
        bad_synthesis = "Quantum computers break modern cryptographic schemes within minutes [99]."
        res_bad = CitationValidator.validate_report(bad_synthesis, retrieved_chunks)
        self.assertEqual(res_bad['total_citations'], 1)
        self.assertEqual(res_bad['valid_citations_count'], 0)
        self.assertEqual(res_bad['hallucinated_citations_count'], 1)
        self.assertEqual(res_bad['citation_precision'], 0.0)
