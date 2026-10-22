import os
import tempfile
import pytest
from django.test import TestCase

from core.models import Document, DocumentChunk, Claim, IngestionStatus
from ingestion.parsers import DocumentParser
from ingestion.chunker import DocumentChunker
from ingestion.pipeline import IngestionPipeline, DuplicateDocumentError


@pytest.mark.django_db
class IngestionPipelineTests(TestCase):

    def setUp(self):
        self.pipeline = IngestionPipeline()
        self.sample_text = (
            "Title: Advanced Empirical Evaluation of Hybrid Retrieval Systems\n"
            "Authors: Elena Vance, Marcus Thorne\n\n"
            "Abstract\n"
            "In this study, we demonstrate that hybrid retrieval architectures combining sparse lexical "
            "weighting with dense semantic embeddings outperform unimodal baselines by 24.8% on technical QA.\n\n"
            "1. Introduction\n"
            "Retrieval systems must balance out-of-distribution keyword precision with high-level semantic generalization.\n\n"
            "2. Experimental Findings\n"
            "Our results demonstrate that BM25 provides superior token precision for technical acronyms, "
            "whereas dense vectors excel at query paraphrasing. We conclude that hybrid integration is optimal."
        )

    def test_parser_metadata_and_sections(self):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            f.write(self.sample_text)
            temp_path = f.name

        try:
            parsed = DocumentParser.parse(temp_path, file_type='txt')
            self.assertEqual(parsed['title'], "Advanced Empirical Evaluation of Hybrid Retrieval Systems")
            self.assertIn("Elena Vance", parsed['authors'])
            self.assertIn("Marcus Thorne", parsed['authors'])
            self.assertTrue(len(parsed['pages']) >= 1)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_chunker_offset_preservation(self):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            f.write(self.sample_text)
            temp_path = f.name

        try:
            parsed = DocumentParser.parse(temp_path, file_type='txt')
            chunker = DocumentChunker(target_chars=300, overlap_chars=50)
            chunks = chunker.chunk_document(parsed)

            self.assertTrue(len(chunks) >= 1)
            first_chunk = chunks[0]
            self.assertIn('start_char', first_chunk)
            self.assertIn('end_char', first_chunk)
            self.assertIn('page_number', first_chunk)
            self.assertEqual(first_chunk['page_number'], 1)
            self.assertTrue(first_chunk['end_char'] > first_chunk['start_char'])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_full_pipeline_ingestion_and_cascading_delete(self):
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            f.write(self.sample_text)
            temp_path = f.name

        try:
            # 1. Ingest
            doc = self.pipeline.process_file(temp_path, original_name="hybrid_retrieval.txt")
            self.assertEqual(doc.ingestion_status, IngestionStatus.COMPLETED)
            self.assertTrue(doc.chunks.count() >= 1)
            self.assertTrue(doc.claims.count() >= 1)
            doc_id = doc.id

            # 2. Duplicate detection
            with self.assertRaises(DuplicateDocumentError):
                self.pipeline.process_file(temp_path, original_name="hybrid_retrieval.txt")

            # 3. Cascading Deletion
            doc.delete()
            self.assertEqual(Document.objects.filter(id=doc_id).count(), 0)
            self.assertEqual(DocumentChunk.objects.filter(document_id=doc_id).count(), 0)
            self.assertEqual(Claim.objects.filter(document_id=doc_id).count(), 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
