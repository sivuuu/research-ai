from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import (
    Claim, ClaimRelationship, ReviewDecision,
    ReviewStatus, RelationshipStatus, RelationshipType, Document
)
from core.serializers import ClaimSerializer, ClaimRelationshipSerializer


class ClaimListView(APIView):
    """Lists claims with rich filtering across documents, review status, and entities."""

    def get(self, request):
        qs = Claim.objects.select_related('document', 'chunk').all()

        doc_id = request.query_params.get('document_id')
        if doc_id:
            qs = qs.filter(document_id=doc_id)

        review_status = request.query_params.get('review_status')
        if review_status:
            qs = qs.filter(review_status=review_status)

        entity = request.query_params.get('entity')
        if entity:
            qs = qs.filter(entities__icontains=entity)

        min_conf = request.query_params.get('min_confidence')
        if min_conf:
            qs = qs.filter(confidence__gte=float(min_conf))

        serializer = ClaimSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'claims': serializer.data
        })


class ClaimDetailView(APIView):
    """Retrieves full provenance and relations for a single claim."""

    def get(self, request, pk):
        claim = get_object_or_404(Claim.objects.select_related('document', 'chunk'), pk=pk)
        return Response(ClaimSerializer(claim).data)


class ClaimReviewView(APIView):
    """Allows a human researcher to accept, reject, or flag a claim."""

    def post(self, request, pk):
        claim = get_object_or_404(Claim, pk=pk)
        decision_val = request.data.get('decision', 'ACCEPT').upper()
        notes = request.data.get('notes', '')

        status_map = {
            'ACCEPT': ReviewStatus.ACCEPTED,
            'REJECT': ReviewStatus.REJECTED,
            'FLAG': ReviewStatus.FLAGGED,
        }
        new_status = status_map.get(decision_val, ReviewStatus.ACCEPTED)
        old_status = claim.review_status

        claim.review_status = new_status
        claim.save()

        ReviewDecision.objects.create(
            claim=claim,
            decision=decision_val,
            reviewer_notes=notes,
            previous_value={'review_status': old_status},
            new_value={'review_status': new_status}
        )

        return Response({
            'message': f"Claim {claim.id} updated to {new_status}",
            'claim': ClaimSerializer(claim).data
        })


class ClaimRelationshipListView(APIView):
    """Lists inter-claim relationships with filters by type and review status."""

    def get(self, request):
        qs = ClaimRelationship.objects.select_related(
            'source_claim__document', 'target_claim__document'
        ).all()

        rel_type = request.query_params.get('type')
        if rel_type:
            qs = qs.filter(relationship_type=rel_type)

        rel_status = request.query_params.get('status')
        if rel_status:
            qs = qs.filter(status=rel_status)

        serializer = ClaimRelationshipSerializer(qs, many=True)
        return Response({
            'count': qs.count(),
            'relationships': serializer.data
        })


class RelationshipReviewView(APIView):
    """Human-in-the-loop review of claim relationships (especially contradictions)."""

    def post(self, request, pk):
        rel = get_object_or_404(ClaimRelationship, pk=pk)
        decision_val = request.data.get('decision', 'ACCEPT').upper()  # ACCEPT, REJECT, MODIFY
        notes = request.data.get('notes', '')
        corrected_type = request.data.get('corrected_type')

        old_status = rel.status
        old_type = rel.relationship_type

        if decision_val == 'ACCEPT':
            rel.status = RelationshipStatus.ACCEPTED
        elif decision_val == 'REJECT':
            rel.status = RelationshipStatus.REJECTED
        elif decision_val == 'MODIFY' and corrected_type:
            rel.relationship_type = corrected_type
            rel.status = RelationshipStatus.ACCEPTED

        rel.save()

        ReviewDecision.objects.create(
            relationship=rel,
            decision=decision_val,
            reviewer_notes=notes,
            previous_value={'status': old_status, 'type': old_type},
            new_value={'status': rel.status, 'type': rel.relationship_type}
        )

        return Response({
            'message': f"Relationship {rel.id} review recorded.",
            'relationship': ClaimRelationshipSerializer(rel).data
        })


class ContradictionQueueView(APIView):
    """Dedicated queue for reviewing detected contradictions and tensions."""

    def get(self, request):
        contradictions = ClaimRelationship.objects.select_related(
            'source_claim__document', 'target_claim__document'
        ).filter(relationship_type=RelationshipType.CONTRADICTS)

        status_param = request.query_params.get('status')
        if status_param:
            contradictions = contradictions.filter(status=status_param)

        serializer = ClaimRelationshipSerializer(contradictions, many=True)
        return Response({
            'count': contradictions.count(),
            'contradictions': serializer.data
        })


class CrossPaperComparisonMatrixView(APIView):
    """Generates cross-paper comparison matrix across all or selected documents."""

    def post(self, request):
        doc_ids = request.data.get('document_ids', [])
        topic = request.data.get('topic')

        docs_qs = Document.objects.filter(ingestion_status='COMPLETED')
        if doc_ids:
            docs_qs = docs_qs.filter(id__in=doc_ids)

        documents = list(docs_qs)
        if not documents:
            return Response({'documents': [], 'matrix': []})

        # Collect claims for each document
        claims_by_doc = {}
        for d in documents:
            c_qs = d.claims.all()
            if topic:
                c_qs = c_qs.filter(claim_text__icontains=topic)
            claims_by_doc[str(d.id)] = list(c_qs)

        # Build feature/entity rows
        all_entities = set()
        for d in documents:
            for c in claims_by_doc.get(str(d.id), []):
                for e in (c.entities or []):
                    all_entities.add(e)

        if not all_entities:
            all_entities = {'Methodology & Findings', 'Latency & Efficiency', 'Accuracy & Faithfulness'}

        matrix_rows = []
        for entity in sorted(all_entities):
            row_cells = []
            for d in documents:
                doc_claims = [c for c in claims_by_doc.get(str(d.id), []) if entity.lower() in [e.lower() for e in (c.entities or [])]]
                if not doc_claims:
                    # Generic claim fallback
                    doc_claims = claims_by_doc.get(str(d.id), [])[:1]

                cell_claims = [{
                    'claim_id': c.id,
                    'text': c.claim_text,
                    'page': c.page_number,
                    'confidence': c.confidence,
                    'status': c.review_status
                } for c in doc_claims[:2]]

                row_cells.append({
                    'document_id': str(d.id),
                    'document_title': d.title,
                    'claims': cell_claims,
                    'has_evidence': len(cell_claims) > 0
                })

            matrix_rows.append({
                'topic_or_entity': entity,
                'cells': row_cells
            })

        return Response({
            'documents': [{
                'id': str(d.id),
                'title': d.title,
                'authors': d.authors,
                'claims_count': len(claims_by_doc.get(str(d.id), []))
            } for d in documents],
            'matrix': matrix_rows
        })
