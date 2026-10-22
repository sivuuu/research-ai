from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class ResearchState(TypedDict):
    original_query: str
    query_id: Optional[str]
    mode: str
    subquestions: List[str]
    retrieved_passages: List[Dict[str, Any]]
    extracted_claims: List[Dict[str, Any]]
    cross_comparisons: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    evidence_gaps: List[str]
    raw_synthesis: str
    validated_citations: List[Dict[str, Any]]
    citation_metrics: Dict[str, Any]
    final_report: Dict[str, Any]
    current_step: str
    step_history: List[Dict[str, Any]]
    retry_count: int
    max_retries: int
    is_sufficient_evidence: bool
    status: str
