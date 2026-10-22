import os
import hashlib
from typing import Dict, Any, Optional
from django.conf import settings
from django.db import transaction

from core.models import Document, DocumentChunk, Claim, Entity, IngestionStatus
from .parsers import DocumentParser
from .chunker import DocumentChunker
from retrieval.embeddings import EmbeddingEngine
from claims.extractor import ClaimExtractor
from claims.comparator import EvidenceComparator


class DuplicateDocumentError(Exception):
    def __init__(self, message: str, existing_doc_id: str):
        super().__init__(message)
        self.existing_doc_id = existing_doc_id


class IngestionPipeline:
    """End-to-end ingestion pipeline for research papers and technical documents."""

    def __init__(self):
        self.chunker = DocumentChunker(target_chars=1400, overlap_chars=200)
        self.embedder = EmbeddingEngine()
        self.claim_extractor = ClaimExtractor()

    def process_file(
        self,
        file_path: str,
        original_name: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> Document:
        file_name = original_name or os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()
        calc_type = file_type or ('pdf' if ext == '.pdf' else 'txt')

        # 1. Validate file constraints
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 30) * 1024 * 1024
        if file_size > max_size:
            raise ValueError(f"File exceeds maximum allowed size ({settings.MAX_UPLOAD_SIZE_MB}MB).")

        # 2. Hash calculation and duplicate detection
        file_hash = self._calculate_sha256(file_path)
        existing_doc = Document.objects.filter(file_hash=file_hash).first()
        if existing_doc:
            raise DuplicateDocumentError(
                f"Document '{file_name}' has already been ingested with ID: {existing_doc.id}",
                existing_doc_id=str(existing_doc.id)
            )

        # 3. Create initial Document record
        doc = Document.objects.create(
            title=os.path.splitext(file_name)[0].replace('_', ' ').title(),
            file_name=file_name,
            file_path=file_path,
            file_hash=file_hash,
            file_size_bytes=file_size,
            file_type=calc_type,
            ingestion_status=IngestionStatus.PARSING
        )

        try:
            # 4. Parsing
            parsed = DocumentParser.parse(file_path, file_type=calc_type)
            doc.title = parsed.get('title') or doc.title
            doc.authors = parsed.get('authors') or []
            doc.publication_date = parsed.get('publication_date')
            doc.publication_details = parsed.get('publication_details')
            doc.abstract = parsed.get('abstract') or ""
            doc.total_pages = parsed.get('total_pages', 1)
            doc.ingestion_status = IngestionStatus.EMBEDDING
            doc.save()

            # 5. Chunking
            raw_chunks = self.chunker.chunk_document(parsed)
            if not raw_chunks:
                # Handle single passage
                raw_chunks = [{
                    'chunk_index': 0,
                    'page_number': 1,
                    'section_title': 'General',
                    'text': parsed.get('abstract', '') or doc.title,
                    'start_char': 0,
                    'end_char': len(parsed.get('abstract', '') or doc.title),
                    'token_count': len((parsed.get('abstract', '') or doc.title).split()),
                    'metadata': {}
                }]

            # 6. Embeddings and Chunk creation
            chunk_objs = []
            for rc in raw_chunks:
                emb = self.embedder.embed_text(rc['text'])
                chunk_obj = DocumentChunk(
                    document=doc,
                    chunk_index=rc['chunk_index'],
                    page_number=rc['page_number'],
                    section_title=rc['section_title'],
                    text=rc['text'],
                    start_char=rc['start_char'],
                    end_char=rc['end_char'],
                    token_count=rc['token_count'],
                    embedding=emb,
                    metadata=rc.get('metadata', {})
                )
                chunk_objs.append(chunk_obj)

            with transaction.atomic():
                DocumentChunk.objects.bulk_create(chunk_objs)

            # 7. Extract Claims & Entities
            doc.ingestion_status = IngestionStatus.EXTRACTING_CLAIMS
            doc.save()

            saved_chunks = list(doc.chunks.all().order_by('chunk_index'))
            extracted_claims = []
            all_doc_entities = set()

            for chunk in saved_chunks:
                c_list = self.claim_extractor.extract_from_chunk(chunk)
                for item in c_list:
                    claim_obj = Claim(
                        id=item['id'],
                        document=doc,
                        chunk=chunk,
                        page_number=item.get('page_number', chunk.page_number),
                        section_title=item.get('section_title', chunk.section_title),
                        claim_text=item['claim_text'],
                        supporting_passage=item['supporting_passage'],
                        confidence=item.get('confidence', 0.85),
                        entities=item.get('entities', []),
                    )
                    extracted_claims.append(claim_obj)
                    for e in item.get('entities', []):
                        all_doc_entities.add(e)

            if extracted_claims:
                with transaction.atomic():
                    Claim.objects.bulk_create(extracted_claims)

            # Register entities in DB
            for ent_name in all_doc_entities:
                ent, _ = Entity.objects.get_or_create(
                    name=ent_name,
                    defaults={'entity_type': 'CONCEPT', 'frequency': 1}
                )
                ent.documents.add(doc)
                ent.frequency = ent.documents.count()
                ent.save()

            # 8. Compare claims across documents for initial graph links
            EvidenceComparator.compare_document_claims(str(doc.id))

            # 9. Mark Completed
            doc.ingestion_status = IngestionStatus.COMPLETED
            doc.save()
            return doc

        except Exception as e:
            doc.ingestion_status = IngestionStatus.FAILED
            doc.error_message = str(e)
            doc.save()
            raise

    @staticmethod
    def _calculate_sha256(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
