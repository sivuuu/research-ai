import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'researchgraph.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import Document, Claim, ClaimRelationship
from ingestion.pipeline import IngestionPipeline, DuplicateDocumentError
from claims.comparator import EvidenceComparator


def seed():
    print("🌱 Starting ResearchGraph AI seeding...")
    pipeline = IngestionPipeline()
    sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sample_documents')

    sample_files = [
        'graphrag_overview.pdf',
        'retrieval_augmented_generation.txt',
        'hallucination_mitigation_survey.txt',
    ]

    ingested_docs = []
    for file_name in sample_files:
        fpath = os.path.join(sample_dir, file_name)
        if not os.path.exists(fpath):
            print(f"⚠️  File not found: {fpath}, skipping.")
            continue

        try:
            print(f"📄 Ingesting {file_name}...")
            doc = pipeline.process_file(file_path=fpath, original_name=file_name)
            ingested_docs.append(doc)
            print(f"   ✅ Ingested: '{doc.title}' ({doc.chunks.count()} chunks, {doc.claims.count()} claims)")
        except DuplicateDocumentError as e:
            print(f"   ℹ️  Already ingested: {e}")
            existing_doc = Document.objects.filter(file_name=file_name).first()
            if existing_doc:
                ingested_docs.append(existing_doc)
        except Exception as e:
            print(f"   ❌ Ingestion failed for {file_name}: {e}")

    # Run cross-document claim comparisons
    print("🔗 Performing cross-paper claim comparisons...")
    for doc in ingested_docs:
        EvidenceComparator.compare_document_claims(str(doc.id))

    # Ensure at least one explicit contradiction is flagged for human review
    c_tension1 = Claim.objects.filter(claim_text__icontains="contrary to common assumptions").first() or Claim.objects.first()
    c_tension2 = Claim.objects.filter(claim_text__icontains="GraphRAG significantly outperforms").first() or Claim.objects.last()
    if c_tension1 and c_tension2 and c_tension1.id != c_tension2.id:
        ClaimRelationship.objects.update_or_create(
            source_claim=c_tension1,
            target_claim=c_tension2,
            relationship_type='CONTRADICTS',
            defaults={
                'confidence': 0.88,
                'evidence_summary': "Direct empirical tension: Paper demonstrates that sparse lexical search outperforms dense vector mechanisms on rare technical identifiers, challenging universal dense RAG superiority.",
                'status': 'FLAGGED_FOR_HUMAN_REVIEW'
            }
        )


    rel_count = ClaimRelationship.objects.count()
    contradictions_count = ClaimRelationship.objects.filter(relationship_type='CONTRADICTS').count()
    print(f"✨ Seeding complete! Database has {Document.objects.count()} documents, {Claim.objects.count()} claims, and {rel_count} relationships ({contradictions_count} contradictions flagged).")


if __name__ == '__main__':
    seed()
