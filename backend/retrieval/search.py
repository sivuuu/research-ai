import re
import math
from typing import List, Dict, Any, Optional
from django.conf import settings
from core.models import Document, DocumentChunk
from .embeddings import EmbeddingEngine


class HybridRetriever:
    """
    Combines dense semantic retrieval and lexical keyword matching with
    metadata filtering and Reciprocal Rank Fusion (RRF).
    """

    def __init__(self):
        self.embedder = EmbeddingEngine()

    def search(
        self,
        query: str,
        top_k: int = 5,
        method: str = "hybrid",  # "vector", "lexical", or "hybrid"
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.15
    ) -> List[Dict[str, Any]]:
        filters = filters or {}
        chunks_qs = DocumentChunk.objects.select_related('document').filter(
            document__ingestion_status='COMPLETED'
        )

        # Apply metadata filters
        doc_ids = filters.get('document_ids')
        if doc_ids:
            chunks_qs = chunks_qs.filter(document_id__in=doc_ids)

        page_min = filters.get('page_min')
        if page_min:
            chunks_qs = chunks_qs.filter(page_number__gte=int(page_min))

        page_max = filters.get('page_max')
        if page_max:
            chunks_qs = chunks_qs.filter(page_number__lte=int(page_max))

        section = filters.get('section')
        if section:
            chunks_qs = chunks_qs.filter(section_title__icontains=section)

        all_chunks = list(chunks_qs)
        if not all_chunks:
            return []

        if method == "vector":
            results = self._vector_search(query, all_chunks, top_k)
        elif method == "lexical":
            results = self._lexical_search(query, all_chunks, top_k)
        else:  # hybrid
            results = self._hybrid_search(query, all_chunks, top_k)

        # Filter by minimum score
        filtered_results = [r for r in results if r['score'] >= min_score]
        return filtered_results[:top_k]

    def _vector_search(self, query: str, chunks: List[DocumentChunk], top_k: int) -> List[Dict[str, Any]]:
        query_vec = self.embedder.embed_text(query)
        scored = []

        for chunk in chunks:
            chunk_vec = chunk.embedding
            if not chunk_vec:
                continue
            sim = self._cosine_similarity(query_vec, chunk_vec)
            scored.append({
                'chunk': chunk,
                'score': round(float(sim), 4),
                'method': 'vector'
            })

        scored.sort(key=lambda x: x['score'], reverse=True)
        return [self._format_result(item['chunk'], item['score'], 'vector', rank=i+1) for i, item in enumerate(scored[:top_k * 2])]

    def _lexical_search(self, query: str, chunks: List[DocumentChunk], top_k: int) -> List[Dict[str, Any]]:
        terms = [t.lower() for t in re.findall(r'\b[a-z0-9_\-]{2,}\b', query.lower())]
        if not terms:
            return []

        scored = []
        for chunk in chunks:
            text_lower = chunk.text.lower()
            section_lower = (chunk.section_title or "").lower()
            doc_title_lower = chunk.document.title.lower()

            score = 0.0
            matched_terms = 0
            for term in terms:
                # Term frequency in text
                count = text_lower.count(term)
                if count > 0:
                    matched_terms += 1
                    score += 1.0 + math.log(count)

                # Heading / title boost
                if term in section_lower:
                    score += 2.0
                if term in doc_title_lower:
                    score += 1.5

            if matched_terms > 0:
                # Coverage ratio bonus
                coverage = matched_terms / len(terms)
                final_score = (score / (len(terms) * 3.0)) * (0.5 + 0.5 * coverage)
                scored.append({
                    'chunk': chunk,
                    'score': round(min(1.0, float(final_score)), 4),
                    'method': 'lexical'
                })

        scored.sort(key=lambda x: x['score'], reverse=True)
        return [self._format_result(item['chunk'], item['score'], 'lexical', rank=i+1) for i, item in enumerate(scored[:top_k * 2])]

    def _hybrid_search(self, query: str, chunks: List[DocumentChunk], top_k: int) -> List[Dict[str, Any]]:
        vector_res = self._vector_search(query, chunks, top_k * 2)
        lexical_res = self._lexical_search(query, chunks, top_k * 2)

        rrf_scores = {}
        chunk_map = {}

        # 60 is standard RRF constant k
        k_const = 60.0

        for r in vector_res:
            c_id = r['chunk_id']
            chunk_map[c_id] = r
            rank = r['rank']
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k_const + rank))

        for r in lexical_res:
            c_id = r['chunk_id']
            if c_id not in chunk_map:
                chunk_map[c_id] = r
            rank = r['rank']
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (k_const + rank))

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        vec_scores = {r['chunk_id']: r['score'] for r in vector_res}
        lex_scores = {r['chunk_id']: r['score'] for r in lexical_res}

        hybrid_results = []
        for i, cid in enumerate(sorted_cids[:top_k]):
            item = dict(chunk_map[cid])
            vs = vec_scores.get(cid, 0.0)
            ls = lex_scores.get(cid, 0.0)
            combined_score = round(vs * 0.6 + ls * 0.4, 4)
            item['score'] = combined_score
            item['retrieval_method'] = 'hybrid'
            item['rank'] = i + 1
            hybrid_results.append(item)

        return hybrid_results

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        min_len = min(len(vec_a), len(vec_b))
        dot = sum(vec_a[i] * vec_b[i] for i in range(min_len))
        # Embeddings from EmbeddingEngine are normalized unit vectors
        return max(0.0, min(1.0, dot))

    @staticmethod
    def _format_result(chunk: DocumentChunk, score: float, method: str, rank: int) -> Dict[str, Any]:
        return {
            'chunk_id': str(chunk.id),
            'document_id': str(chunk.document.id),
            'document_title': chunk.document.title,
            'file_name': chunk.document.file_name,
            'page_number': chunk.page_number,
            'section_title': chunk.section_title or "General",
            'text': chunk.text,
            'score': score,
            'retrieval_method': method,
            'rank': rank,
            'start_char': chunk.start_char,
            'end_char': chunk.end_char,
        }
