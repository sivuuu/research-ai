import re
from typing import List, Dict, Any

class Reranker:
    """
    Reranks retrieved candidate passages using exact term matches, phrase alignment,
    and entity density to refine ranking precision.
    """

    @classmethod
    def rerank(cls, query: str, candidates: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r'\b[a-z0-9_\-]{3,}\b', query_lower))

        reranked = []
        for item in candidates:
            text_lower = item['text'].lower()
            section_lower = item.get('section_title', '').lower()
            original_score = item.get('score', 0.5)

            boost = 0.0

            # 1. Exact phrase match boost
            if len(query_lower) > 10 and query_lower in text_lower:
                boost += 0.25

            # 2. Section heading relevance boost
            if any(w in section_lower for w in query_words):
                boost += 0.15

            # 3. Density of query terms in the text
            matched_words = sum(1 for w in query_words if w in text_lower)
            density_ratio = matched_words / max(1, len(query_words))
            boost += 0.20 * density_ratio

            combined_score = round(min(1.0, original_score * 0.6 + (0.5 + boost) * 0.4), 4)

            item_copy = dict(item)
            item_copy['original_score'] = original_score
            item_copy['score'] = combined_score
            reranked.append(item_copy)

        reranked.sort(key=lambda x: x['score'], reverse=True)
        for i, item in enumerate(reranked):
            item['rank'] = i + 1

        return reranked[:top_k]
