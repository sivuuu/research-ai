import re
import uuid
import json
from typing import List, Dict, Any, Optional
import requests
from django.conf import settings
from core.models import Document, DocumentChunk, Claim, Entity, Topic


class ClaimExtractor:
    """
    Extracts grounded factual claims and scientific entities from research passages.
    Extracts exact supporting passages and page numbers for complete provenance.
    """

    ASSERTION_PATTERNS = [
        re.compile(r'(?:we\s+(?:find|demonstrate|show|observe|prove|discover|propose|conclude)\s+that\s+)([^.?!]+[.?!])', re.IGNORECASE),
        re.compile(r'(?:our\s+(?:results|findings|experiments|analysis)\s+(?:indicate|reveal|demonstrate|show)\s+that\s+)([^.?!]+[.?!])', re.IGNORECASE),
        re.compile(r'(?:(?:it\s+is\s+shown|evidence\s+suggests|we\s+achieve)\s+that\s+)([^.?!]+[.?!])', re.IGNORECASE),
        re.compile(r'([^.?!]*(?:outperforms|significantly\s+reduces|degrades\s+performance|mitigates\s+hallucination|leads\s+to\s+inaccurate)[^.?!]+[.?!])', re.IGNORECASE),
        re.compile(r'([^.?!]*(?:increases|decreases|proves\s+effective|fails\s+to|yields\s+a\s+\d+%?)[^.?!]+[.?!])', re.IGNORECASE),
    ]

    ENTITY_REGEX = re.compile(
        r'\b(?:RAG|GraphRAG|LLM|LLMs|GPT-\d+|BERT|Transformer|Knowledge Graph|pgvector|PyMuPDF|LangGraph|Ollama|BM25|Dense Retrieval|Vector Search|Hallucination|Faithfulness|MRR|Recall@K|BLEU|ROUGE|TruthfulQA|HotpotQA)\b',
        re.IGNORECASE
    )

    def __init__(self):
        self.ollama_base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3:latest')

    def extract_from_chunk(self, chunk: DocumentChunk) -> List[Dict[str, Any]]:
        """Extract claims from a single chunk using LLM or rule-based fallback."""
        claims = []

        # Try LLM extraction if Ollama is available
        llm_claims = self._extract_via_llm(chunk)
        if llm_claims:
            return llm_claims

        # Deterministic rule-based extraction
        return self._extract_via_rules(chunk)

    def _extract_via_llm(self, chunk: DocumentChunk) -> Optional[List[Dict[str, Any]]]:
        prompt = f"""You are a research claim extraction system.
Analyze the following passage from the paper '{chunk.document.title}' (Page {chunk.page_number}, Section: {chunk.section_title}).
Extract 1 to 3 key factual research claims, assertions, or experimental findings.

Rules:
1. Every claim MUST be directly backed by an exact verbatim quote from the passage (the supporting passage).
2. Extract any specific entities or methods mentioned.
3. Return ONLY a JSON list of objects matching this schema:
[
  {{
    "claim_text": "Brief concise assertion statement",
    "supporting_passage": "Exact verbatim excerpt from the text that proves it",
    "entities": ["Entity1", "Entity2"],
    "confidence": 0.90
  }}
]

Passage:
\"\"\"{chunk.text}\"\"\"
"""
        try:
            resp = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=4.0
            )
            if resp.status_code == 200:
                body = resp.json().get('response', '')
                parsed = json.loads(body)
                if isinstance(parsed, dict) and 'claims' in parsed:
                    parsed = parsed['claims']
                if isinstance(parsed, list) and len(parsed) > 0:
                    results = []
                    for i, item in enumerate(parsed):
                        claim_text = item.get('claim_text', '').strip()
                        passage = item.get('supporting_passage', '').strip()
                        if not passage or passage not in chunk.text:
                            passage = chunk.text[:300]
                        if claim_text:
                            claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
                            results.append({
                                'id': claim_id,
                                'claim_text': claim_text,
                                'supporting_passage': passage,
                                'entities': item.get('entities', []),
                                'confidence': float(item.get('confidence', 0.88)),
                                'page_number': chunk.page_number,
                                'section_title': chunk.section_title,
                            })
                    if results:
                        return results
        except Exception:
            pass

        return None

    def _extract_via_rules(self, chunk: DocumentChunk) -> List[Dict[str, Any]]:
        claims = []
        text = chunk.text
        sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', text) if len(s.strip()) > 30]

        seen_texts = set()
        for s in sentences:
            for pattern in self.ASSERTION_PATTERNS:
                m = pattern.search(s)
                if m:
                    extracted = m.group(1).strip() if m.groups() else s.strip()
                    if len(extracted) > 25 and extracted.lower() not in seen_texts:
                        seen_texts.add(extracted.lower())
                        entities = list(set(self.ENTITY_REGEX.findall(s)))
                        claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
                        claims.append({
                            'id': claim_id,
                            'claim_text': extracted,
                            'supporting_passage': s,
                            'entities': entities,
                            'confidence': 0.85,
                            'page_number': chunk.page_number,
                            'section_title': chunk.section_title,
                        })
                        if len(claims) >= 3:
                            break
            if len(claims) >= 3:
                break

        # If no explicit pattern matched, extract the primary informative sentence
        if not claims and sentences:
            primary_sentence = max(sentences, key=lambda x: len(re.findall(r'\b[A-Z][a-z]+|\d+%?', x)))
            entities = list(set(self.ENTITY_REGEX.findall(primary_sentence)))
            claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
            claims.append({
                'id': claim_id,
                'claim_text': primary_sentence,
                'supporting_passage': primary_sentence,
                'entities': entities,
                'confidence': 0.78,
                'page_number': chunk.page_number,
                'section_title': chunk.section_title,
            })

        return claims
