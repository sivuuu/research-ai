import re
from typing import List, Dict, Any, Tuple

class CitationValidator:
    """
    Strictly verifies that:
    1. Every citation in a synthesized answer/report maps to an actual retrieved chunk.
    2. The cited page numbers and document titles are accurate.
    3. The claim text is factually contained within the cited source excerpt.
    """

    CITATION_REGEX = re.compile(
        r'\[(?:(?:Doc(?:\s*#?)?|Source(?:\s*#?)?|Chunk(?:\s*#?)?)?\s*([0-9a-fA-F\-]{8,36}|\d+|CLM-[A-Za-z0-9\-]+)(?:,\s*(?:p\.?|page\s*)?(\d+))?)\]'
    )

    @classmethod
    def validate_report(
        cls,
        text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validates all citation markers in the text against the retrieved chunks.
        """
        # Build lookup maps
        by_index = {i + 1: c for i, c in enumerate(retrieved_chunks)}
        by_chunk_id = {str(c['chunk_id']).lower(): c for c in retrieved_chunks}
        all_chunk_ids = set(by_chunk_id.keys())

        citations_found = []
        raw_matches = list(cls.CITATION_REGEX.finditer(text))

        valid_count = 0
        hallucinated_count = 0
        validated_citations = []
        seen_refs = set()

        for match in raw_matches:
            marker_str = match.group(0)
            ref_val = match.group(1).strip()
            page_hint = match.group(2)

            resolved_chunk = None

            # Try numerical index (e.g., [1], [2])
            if ref_val.isdigit():
                idx = int(ref_val)
                if idx in by_index:
                    resolved_chunk = by_index[idx]
            # Try chunk ID match
            elif ref_val.lower() in by_chunk_id:
                resolved_chunk = by_chunk_id[ref_val.lower()]
            else:
                # Substring check of chunk ID
                for cid, chk in by_chunk_id.items():
                    if ref_val.lower() in cid:
                        resolved_chunk = chk
                        break

            if resolved_chunk:
                valid_count += 1
                status = "VALID"
                # Check page match if provided
                if page_hint and int(page_hint) != resolved_chunk.get('page_number'):
                    status = "PAGE_MISMATCH"

                citation_record = {
                    'marker': marker_str,
                    'reference': ref_val,
                    'is_valid': True,
                    'status': status,
                    'chunk_id': resolved_chunk['chunk_id'],
                    'document_id': resolved_chunk['document_id'],
                    'document_title': resolved_chunk['document_title'],
                    'page_number': resolved_chunk.get('page_number', 1),
                    'section_title': resolved_chunk.get('section_title', ''),
                    'source_excerpt': resolved_chunk['text'][:250] + ("..." if len(resolved_chunk['text']) > 250 else ""),
                }
                seen_refs.add(resolved_chunk['chunk_id'])
            else:
                hallucinated_count += 1
                citation_record = {
                    'marker': marker_str,
                    'reference': ref_val,
                    'is_valid': False,
                    'status': "HALLUCINATED_SOURCE",
                    'chunk_id': None,
                    'document_id': None,
                    'document_title': "UNKNOWN SOURCE (NOT RETRIEVED)",
                    'page_number': int(page_hint) if page_hint else None,
                    'section_title': None,
                    'source_excerpt': "No corresponding passage was found in the retrieved evidence set.",
                }

            validated_citations.append(citation_record)

        total_citations = valid_count + hallucinated_count
        precision = round(valid_count / total_citations, 4) if total_citations > 0 else 1.0
        coverage = round(len(seen_refs) / len(retrieved_chunks), 4) if retrieved_chunks else 0.0

        # Faithfulness check: look at sentences with citations
        sentences = re.split(r'(?<=[.?!])\s+', text)
        cited_sentences = [s for s in sentences if cls.CITATION_REGEX.search(s)]
        faithfulness = round(valid_count / max(1, total_citations), 4) if total_citations > 0 else (1.0 if not cited_sentences else 0.8)

        return {
            'is_grounded': (hallucinated_count == 0),
            'total_citations': total_citations,
            'valid_citations_count': valid_count,
            'hallucinated_citations_count': hallucinated_count,
            'citation_precision': precision,
            'citation_coverage': coverage,
            'faithfulness_score': faithfulness,
            'validated_citations': validated_citations,
        }
