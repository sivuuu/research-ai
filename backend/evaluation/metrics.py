import re
from typing import List, Dict, Any, Set, Tuple


class EvaluationMetrics:
    """Rigorous evaluation metric calculators for retrieval, citations, claims, and contradictions."""

    @staticmethod
    def recall_at_k(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
        """Recall@K = (retrieved[:k] ∩ expected) / expected"""
        if not expected_ids:
            return 1.0
        top_k = set(retrieved_ids[:k])
        target = set(expected_ids)
        overlap = top_k.intersection(target)
        return len(overlap) / len(target)

    @staticmethod
    def reciprocal_rank(retrieved_ids: List[str], expected_ids: List[str]) -> float:
        """MRR = 1 / rank of first relevant item found in retrieved_ids"""
        target = set(expected_ids)
        for rank, item_id in enumerate(retrieved_ids, 1):
            if item_id in target:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def citation_precision_and_coverage(
        validated_citations: List[Dict[str, Any]],
        expected_sources: List[str]
    ) -> Tuple[float, float]:
        """
        Citation Precision: Valid citations / Total citations
        Citation Coverage: Cited relevant sources / Total expected sources
        """
        if not validated_citations:
            return 1.0, 0.0

        valid_count = sum(1 for c in validated_citations if c.get('is_valid', False))
        precision = valid_count / len(validated_citations)

        cited_doc_or_chunk_ids = set()
        for c in validated_citations:
            if c.get('is_valid', False):
                if c.get('chunk_id'):
                    cited_doc_or_chunk_ids.add(str(c['chunk_id']).lower())
                if c.get('document_id'):
                    cited_doc_or_chunk_ids.add(str(c['document_id']).lower())

        target_set = set(s.lower() for s in expected_sources)
        overlap = cited_doc_or_chunk_ids.intersection(target_set)
        coverage = len(overlap) / len(target_set) if target_set else 1.0

        return round(precision, 4), round(coverage, 4)

    @staticmethod
    def claim_extraction_precision_recall(
        extracted_claims: List[str],
        labeled_claims: List[str],
        match_threshold: float = 0.50
    ) -> Tuple[float, float, float]:
        """
        Evaluates extracted claims against human-annotated ground-truth claims using token Jaccard similarity.
        Returns (precision, recall, f1).
        """
        if not labeled_claims:
            return 1.0, 1.0, 1.0
        if not extracted_claims:
            return 0.0, 0.0, 0.0

        def tokenize(s: str) -> Set[str]:
            return set(re.findall(r'\b[a-z0-9_\-]{3,}\b', s.lower()))

        extracted_tokens = [tokenize(c) for c in extracted_claims]
        labeled_tokens = [tokenize(c) for c in labeled_claims]

        true_positives = 0
        matched_labeled_indices = set()

        for ext_tok in extracted_tokens:
            for l_idx, lab_tok in enumerate(labeled_tokens):
                if l_idx in matched_labeled_indices:
                    continue
                union = ext_tok.union(lab_tok)
                if not union:
                    continue
                jaccard = len(ext_tok.intersection(lab_tok)) / len(union)
                if jaccard >= match_threshold:
                    true_positives += 1
                    matched_labeled_indices.add(l_idx)
                    break

        precision = true_positives / len(extracted_claims) if extracted_claims else 0.0
        recall = len(matched_labeled_indices) / len(labeled_claims) if labeled_claims else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return round(precision, 4), round(recall, 4), round(f1, 4)

    @staticmethod
    def contradiction_detection_precision_recall(
        detected_contradiction_pairs: List[Tuple[str, str]],
        labeled_contradiction_pairs: List[Tuple[str, str]]
    ) -> Tuple[float, float, float]:
        """
        Evaluates whether opposing claim pairs were correctly classified as CONTRADICTS.
        Returns (precision, recall, f1).
        """
        if not labeled_contradiction_pairs:
            return (1.0, 1.0, 1.0) if not detected_contradiction_pairs else (0.0, 1.0, 0.0)
        if not detected_contradiction_pairs:
            return 0.0, 0.0, 0.0

        def normalize_pair(pair: Tuple[str, str]) -> Tuple[str, str]:
            a, b = pair
            return (min(a, b), max(a, b))

        detected_set = {normalize_pair(p) for p in detected_contradiction_pairs}
        labeled_set = {normalize_pair(p) for p in labeled_contradiction_pairs}

        tp = len(detected_set.intersection(labeled_set))
        precision = tp / len(detected_set) if detected_set else 0.0
        recall = tp / len(labeled_set) if labeled_set else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return round(precision, 4), round(recall, 4), round(f1, 4)
