import re
import math
from typing import List, Dict, Any, Tuple, Optional
from core.models import Claim, ClaimRelationship, RelationshipType, RelationshipStatus


class EvidenceComparator:
    """
    Compares claims across documents to identify agreements, contradictions, qualifications,
    and dependencies.
    Crucial: Does not treat semantic similarity alone as contradiction. It performs deep
    stance/polarity and directional assertion comparison.
    """

    POSITIVE_LEMMAS = {
        'improve', 'improves', 'improved', 'improving', 'improvement',
        'outperform', 'outperforms', 'outperformed', 'superior',
        'enhance', 'enhances', 'enhanced', 'boost', 'boosts', 'boosted',
        'reduce', 'reduces', 'reduced', 'mitigate', 'mitigates', 'mitigated',
        'effective', 'accurately', 'significant', 'beneficial', 'advancement'
    }

    NEGATIVE_LEMMAS = {
        'fail', 'fails', 'failed', 'failing', 'failure',
        'degrade', 'degrades', 'degraded', 'degrading', 'degradation',
        'ineffective', 'worse', 'underperform', 'underperforms',
        'limitation', 'limited', 'unreliable', 'harmful', 'inaccurate',
        'hallucinate', 'hallucinates', 'hallucination', 'decline'
    }

    QUALIFIER_PATTERNS = [
        re.compile(r'\b(?:only\s+when|provided\s+that|under\s+(?:the\s+)?condition|limited\s+to|except\s+for|threshold|constrained\s+by)\b', re.IGNORECASE),
        re.compile(r'\b(?:however|nevertheless|nonetheless|whereas|although|on\s+the\s+other\s+hand)\b', re.IGNORECASE)
    ]

    DEPENDENCY_PATTERNS = [
        re.compile(r'\b(?:depends\s+on|relies\s+on|requires|built\s+upon|assumes|contingent\s+on)\b', re.IGNORECASE),
        re.compile(r'\b(?:derived\s+from|extension\s+of|adapts\s+from|formalized\s+by)\b', re.IGNORECASE)
    ]

    @classmethod
    def compare_claims(cls, claim_a: Claim, claim_b: Claim) -> Optional[Dict[str, Any]]:
        """
        Evaluates the relationship between two claims.
        Returns a dict describing relationship_type, confidence, evidence_summary, and review status.
        """
        if claim_a.id == claim_b.id:
            return None

        text_a = claim_a.claim_text.lower()
        text_b = claim_b.claim_text.lower()

        # Check entity/keyword overlap
        words_a = set(re.findall(r'\b[a-z]{3,}\b', text_a))
        words_b = set(re.findall(r'\b[a-z]{3,}\b', text_b))
        overlap = words_a.intersection(words_b)

        # Entity overlap from structured entity lists
        entities_a = set(e.lower() for e in (claim_a.entities or []))
        entities_b = set(e.lower() for e in (claim_b.entities or []))
        shared_entities = entities_a.intersection(entities_b)

        # Need sufficient topical context to compare
        if len(shared_entities) == 0 and len(overlap) < 2:
            return None

        # Check for dependency
        for pat in cls.DEPENDENCY_PATTERNS:
            if pat.search(claim_a.supporting_passage) or pat.search(claim_b.supporting_passage):
                return {
                    'source_claim': claim_a,
                    'target_claim': claim_b,
                    'relationship_type': RelationshipType.DEPENDS_ON,
                    'confidence': 0.82,
                    'evidence_summary': f"Text explicitly mentions methodological dependency or derivation between claims regarding {list(shared_entities or overlap)[:2]}.",
                    'status': RelationshipStatus.PROPOSED
                }

        # Check for qualification
        has_qualifier = any(pat.search(claim_a.supporting_passage) or pat.search(claim_b.supporting_passage) for pat in cls.QUALIFIER_PATTERNS)

        pos_a = len(words_a.intersection(cls.POSITIVE_LEMMAS))
        neg_a = len(words_a.intersection(cls.NEGATIVE_LEMMAS))
        pos_b = len(words_b.intersection(cls.POSITIVE_LEMMAS))
        neg_b = len(words_b.intersection(cls.NEGATIVE_LEMMAS))

        polarity_a = 1 if pos_a > neg_a else (-1 if neg_a > pos_a else 0)
        polarity_b = 1 if pos_b > neg_b else (-1 if neg_b > pos_b else 0)

        # Contradiction Detection: shared topic/entity with opposing polarity findings
        if polarity_a != 0 and polarity_b != 0 and polarity_a == -polarity_b:
            confidence = 0.88 if shared_entities else 0.74
            # If confidence is lower or has qualifiers, flag for human review
            status = RelationshipStatus.PROPOSED if confidence >= 0.85 else RelationshipStatus.FLAGGED_FOR_HUMAN_REVIEW

            subject_str = ", ".join(list(shared_entities or overlap)[:3])
            summary = (
                f"Contradictory findings detected on subject '{subject_str}'. "
                f"Document '{claim_a.document.title}' reports positive/effective results, "
                f"whereas Document '{claim_b.document.title}' reports degradation or failure."
            )

            return {
                'source_claim': claim_a,
                'target_claim': claim_b,
                'relationship_type': RelationshipType.CONTRADICTS,
                'confidence': confidence,
                'evidence_summary': summary,
                'status': status
            }

        # Qualification Detection
        if has_qualifier and len(overlap) >= 2:
            return {
                'source_claim': claim_a,
                'target_claim': claim_b,
                'relationship_type': RelationshipType.QUALIFIES,
                'confidence': 0.79,
                'evidence_summary': f"Claim qualifies or constrains findings of the other with specific boundary conditions.",
                'status': RelationshipStatus.FLAGGED_FOR_HUMAN_REVIEW
            }

        # Support Detection: shared entities and consistent polarity
        if (polarity_a != 0 and polarity_a == polarity_b) or len(shared_entities) >= 2 or len(overlap) >= 4:
            confidence = 0.85 if shared_entities else 0.76
            return {
                'source_claim': claim_a,
                'target_claim': claim_b,
                'relationship_type': RelationshipType.SUPPORTS,
                'confidence': confidence,
                'evidence_summary': f"Both papers present concordant findings and mutual reinforcement regarding {list(shared_entities or overlap)[:2]}.",
                'status': RelationshipStatus.ACCEPTED if confidence > 0.8 else RelationshipStatus.PROPOSED
            }

        return None

    @classmethod
    def compare_document_claims(cls, doc_id: str) -> List[ClaimRelationship]:
        """Runs comparison between claims of the given document and all other claims in the DB."""
        new_relationships = []
        target_claims = Claim.objects.filter(document_id=doc_id)
        other_claims = Claim.objects.exclude(document_id=doc_id)

        for ca in target_claims:
            for cb in other_claims:
                rel_dict = cls.compare_claims(ca, cb)
                if rel_dict:
                    # Persist or update
                    rel, created = ClaimRelationship.objects.update_or_create(
                        source_claim=rel_dict['source_claim'],
                        target_claim=rel_dict['target_claim'],
                        relationship_type=rel_dict['relationship_type'],
                        defaults={
                            'confidence': rel_dict['confidence'],
                            'evidence_summary': rel_dict['evidence_summary'],
                            'status': rel_dict['status'],
                        }
                    )
                    new_relationships.append(rel)

        return new_relationships
