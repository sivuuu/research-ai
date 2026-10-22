from typing import Dict, List, Any, Optional
from core.models import Document, DocumentChunk, Claim, ClaimRelationship, Entity, Topic


class GraphService:
    """
    Constructs an interactive property graph connecting:
    Documents, Authors, Topics, Entities, Claims, and Evidence Passages.
    Stores explicit evidence supporting each edge and enables full provenance traversal.
    """

    @classmethod
    def get_graph(
        cls,
        document_id: Optional[str] = None,
        topic: Optional[str] = None,
        include_evidence_nodes: bool = True
    ) -> Dict[str, Any]:
        nodes = []
        edges = []
        seen_node_ids = set()
        seen_edge_keys = set()

        def add_node(node_id: str, label: str, node_type: str, metadata: Dict[str, Any]):
            if node_id not in seen_node_ids:
                seen_node_ids.add(node_id)
                nodes.append({
                    'id': node_id,
                    'label': label,
                    'type': node_type,
                    'metadata': metadata
                })

        def add_edge(source: str, target: str, rel_type: str, evidence: str = "", metadata: Optional[Dict[str, Any]] = None):
            edge_key = f"{source}->{target}:{rel_type}"
            if edge_key not in seen_edge_keys:
                seen_edge_keys.add(edge_key)
                edges.append({
                    'id': edge_key,
                    'source': source,
                    'target': target,
                    'type': rel_type,
                    'evidence': evidence,
                    'metadata': metadata or {}
                })

        docs_qs = Document.objects.filter(ingestion_status='COMPLETED')
        if document_id:
            docs_qs = docs_qs.filter(id=document_id)

        documents = list(docs_qs)

        # 1. Documents & Authors
        for doc in documents:
            doc_node_id = f"doc_{doc.id}"
            add_node(
                doc_node_id,
                doc.title[:40] + ("..." if len(doc.title) > 40 else ""),
                'document',
                {
                    'full_title': doc.title,
                    'doc_id': str(doc.id),
                    'total_pages': doc.total_pages,
                    'abstract': doc.abstract[:200]
                }
            )

            # Authors
            for author_name in (doc.authors or []):
                if author_name:
                    author_id = f"author_{author_name.replace(' ', '_').lower()}"
                    add_node(author_id, author_name, 'author', {'name': author_name})
                    add_edge(doc_node_id, author_id, 'AUTHORED_BY', f"Document author metadata")

            # Document Topics
            for t_name in (doc.topics or []):
                topic_id = f"topic_{t_name.replace(' ', '_').lower()}"
                add_node(topic_id, t_name, 'topic', {'name': t_name})
                add_edge(doc_node_id, topic_id, 'HAS_TOPIC', f"Subject topic classification")

        # 2. Claims & Evidence Passages
        claims_qs = Claim.objects.select_related('document', 'chunk').filter(document__in=documents)
        claims = list(claims_qs)

        for claim in claims:
            claim_node_id = f"claim_{claim.id}"
            doc_node_id = f"doc_{claim.document_id}"

            add_node(
                claim_node_id,
                claim.claim_text[:45] + ("..." if len(claim.claim_text) > 45 else ""),
                'claim',
                {
                    'claim_id': claim.id,
                    'full_text': claim.claim_text,
                    'page_number': claim.page_number,
                    'section': claim.section_title,
                    'confidence': claim.confidence,
                    'review_status': claim.review_status,
                    'supporting_passage': claim.supporting_passage,
                    'document_title': claim.document.title,
                    'doc_id': str(claim.document.id)
                }
            )

            # Connect Document to Claim
            add_edge(
                doc_node_id,
                claim_node_id,
                'ASSERTS_CLAIM',
                f"Page {claim.page_number}, Section: {claim.section_title or 'General'}",
                {'page': claim.page_number}
            )

            # Evidence Passage Node (if enabled)
            if include_evidence_nodes and claim.chunk:
                passage_node_id = f"passage_{claim.chunk.id}"
                add_node(
                    passage_node_id,
                    f"Passage p.{claim.page_number} [c.{claim.chunk.chunk_index}]",
                    'evidence_passage',
                    {
                        'chunk_id': str(claim.chunk.id),
                        'page_number': claim.chunk.page_number,
                        'text': claim.chunk.text[:250],
                        'section': claim.chunk.section_title
                    }
                )
                add_edge(
                    claim_node_id,
                    passage_node_id,
                    'GROUNDED_IN',
                    claim.supporting_passage[:150]
                )

            # Entities mentioned in Claim
            for ent_name in (claim.entities or []):
                ent_id = f"entity_{ent_name.replace(' ', '_').lower()}"
                add_node(ent_id, ent_name, 'entity', {'name': ent_name})
                add_edge(claim_node_id, ent_id, 'MENTIONS_ENTITY', f"Found in claim text")

        # 3. Inter-claim relationships (Supports, Contradicts, Qualifies, Depends on)
        claim_ids = [c.id for c in claims]
        relationships = ClaimRelationship.objects.select_related(
            'source_claim', 'target_claim'
        ).filter(source_claim_id__in=claim_ids, target_claim_id__in=claim_ids)

        for rel in relationships:
            source_id = f"claim_{rel.source_claim_id}"
            target_id = f"claim_{rel.target_claim_id}"
            add_edge(
                source_id,
                target_id,
                rel.relationship_type,
                rel.evidence_summary,
                {
                    'rel_id': str(rel.id),
                    'confidence': rel.confidence,
                    'status': rel.status
                }
            )

        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'documents_count': len(documents),
                'claims_count': len(claims),
                'relationships_count': relationships.count()
            }
        }
