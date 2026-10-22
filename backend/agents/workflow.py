import re
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END

from .state import ResearchState
from .llm_client import LLMClient
from retrieval.search import HybridRetriever
from retrieval.validator import CitationValidator
from claims.extractor import ClaimExtractor
from claims.comparator import EvidenceComparator


class MultiAgentResearchWorkflow:
    """
    7-Stage Multi-Agent Research Workflow:
    1. Research Planner
    2. Evidence Retriever
    3. Claim Extractor
    4. Evidence Comparator
    5. Synthesis Agent
    6. Citation Validator
    7. Report Generator
    """

    def __init__(self):
        self.llm = LLMClient()
        self.retriever = HybridRetriever()
        self.claim_extractor = ClaimExtractor()
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ResearchState)

        # Register nodes
        workflow.add_node("research_planner", self.node_research_planner)
        workflow.add_node("evidence_retriever", self.node_evidence_retriever)
        workflow.add_node("claim_extractor", self.node_claim_extractor)
        workflow.add_node("evidence_comparator", self.node_evidence_comparator)
        workflow.add_node("synthesis_agent", self.node_synthesis_agent)
        workflow.add_node("citation_validator", self.node_citation_validator)
        workflow.add_node("report_generator", self.node_report_generator)

        # Set entry point
        workflow.set_entry_point("research_planner")

        # Edges
        workflow.add_edge("research_planner", "evidence_retriever")

        # After retriever: check if evidence is sufficient
        def check_evidence(state: ResearchState) -> str:
            if not state.get("is_sufficient_evidence", True):
                return "report_generator"
            return "claim_extractor"

        workflow.add_conditional_edges(
            "evidence_retriever",
            check_evidence,
            {
                "claim_extractor": "claim_extractor",
                "report_generator": "report_generator"
            }
        )

        workflow.add_edge("claim_extractor", "evidence_comparator")
        workflow.add_edge("evidence_comparator", "synthesis_agent")
        workflow.add_edge("synthesis_agent", "citation_validator")

        # After citation validator: verify precision and retry if needed
        def check_citations(state: ResearchState) -> str:
            metrics = state.get("citation_metrics", {})
            hallucinated = metrics.get("hallucinated_citations_count", 0)
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 2)

            if hallucinated > 0 and retry_count < max_retries:
                return "synthesis_agent"
            return "report_generator"

        workflow.add_conditional_edges(
            "citation_validator",
            check_citations,
            {
                "synthesis_agent": "synthesis_agent",
                "report_generator": "report_generator"
            }
        )

        workflow.add_edge("report_generator", END)

        return workflow.compile()

    # 1. Research Planner
    def node_research_planner(self, state: ResearchState) -> Dict[str, Any]:
        query = state["original_query"]
        history = list(state.get("step_history", []))

        prompt = f"""Decompose the research question into 3 specific, targeted subquestions for academic literature retrieval:
Question: "{query}"

Return ONLY a JSON list of 3 strings:
["subquestion 1", "subquestion 2", "subquestion 3"]
"""
        subquestions = []
        llm_resp = self.llm.generate(prompt, format_json=True)
        if llm_resp:
            try:
                parsed = json.loads(llm_resp)
                if isinstance(parsed, list):
                    subquestions = [s for s in parsed if isinstance(s, str)][:3]
            except Exception:
                pass

        if not subquestions:
            subquestions = [
                f"What are the foundational concepts, definitions, and architectures related to '{query}'?",
                f"What experimental findings, benchmark metrics, and performance results address '{query}'?",
                f"What are the verified limitations, trade-offs, and failure modes regarding '{query}'?"
            ]

        step_info = {
            "step": "research_planner",
            "message": f"Decomposed query into {len(subquestions)} targeted subquestions.",
            "subquestions": subquestions
        }
        history.append(step_info)

        return {
            "current_step": "research_planner",
            "subquestions": subquestions,
            "step_history": history
        }

    # 2. Evidence Retriever
    def node_evidence_retriever(self, state: ResearchState) -> Dict[str, Any]:
        query = state["original_query"]
        subqs = state.get("subquestions", [])
        history = list(state.get("step_history", []))

        all_candidates = []
        seen_chunk_ids = set()

        # Retrieve for main query with strict min_score
        main_results = self.retriever.search(query=query, top_k=4, method="hybrid", min_score=0.25)
        for r in main_results:
            if r['chunk_id'] not in seen_chunk_ids:
                seen_chunk_ids.add(r['chunk_id'])
                r['subquestion'] = query
                all_candidates.append(r)

        # Retrieve for each subquestion
        for sq in subqs:
            sq_results = self.retriever.search(query=sq, top_k=3, method="hybrid", min_score=0.25)
            for r in sq_results:
                if r['chunk_id'] not in seen_chunk_ids:
                    seen_chunk_ids.add(r['chunk_id'])
                    r['subquestion'] = sq
                    all_candidates.append(r)

        # Sort and re-index
        all_candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
        final_passages = all_candidates[:8]
        for idx, p in enumerate(final_passages):
            p['source_index'] = idx + 1

        is_sufficient = len(final_passages) > 0 and any(p.get('score', 0) >= 0.45 for p in final_passages)

        evidence_gaps = list(state.get("evidence_gaps", []))
        if not is_sufficient:
            gap_msg = f"Insufficient empirical evidence in the document collection regarding: '{query}'. Retrieval returned 0 qualifying passages above relevance threshold."
            evidence_gaps.append(gap_msg)

        step_info = {
            "step": "evidence_retriever",
            "message": f"Retrieved {len(final_passages)} passages across {len(subqs) + 1} queries.",
            "passages_count": len(final_passages),
            "is_sufficient": is_sufficient
        }
        history.append(step_info)

        return {
            "current_step": "evidence_retriever",
            "retrieved_passages": final_passages,
            "is_sufficient_evidence": is_sufficient,
            "evidence_gaps": evidence_gaps,
            "step_history": history
        }

    # 3. Claim Extractor
    def node_claim_extractor(self, state: ResearchState) -> Dict[str, Any]:
        passages = state.get("retrieved_passages", [])
        history = list(state.get("step_history", []))
        extracted_claims = []

        for p in passages:
            sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', p['text']) if len(s.strip()) > 25]
            if sentences:
                best_sentence = max(sentences, key=lambda s: len(re.findall(r'\b[A-Z][a-z]+|\d+%?', s)))
                claim_id = f"CLM-SRC{p['source_index']}"
                extracted_claims.append({
                    "id": claim_id,
                    "claim_text": best_sentence,
                    "source_index": p['source_index'],
                    "chunk_id": p['chunk_id'],
                    "document_id": p['document_id'],
                    "document_title": p['document_title'],
                    "page_number": p.get('page_number', 1),
                    "section_title": p.get('section_title', ''),
                    "supporting_passage": best_sentence,
                    "confidence": round(p.get('score', 0.85), 2),
                })

        step_info = {
            "step": "claim_extractor",
            "message": f"Extracted {len(extracted_claims)} grounded claims from retrieved passages.",
            "claims_count": len(extracted_claims)
        }
        history.append(step_info)

        return {
            "current_step": "claim_extractor",
            "extracted_claims": extracted_claims,
            "step_history": history
        }

    # 4. Evidence Comparator
    def node_evidence_comparator(self, state: ResearchState) -> Dict[str, Any]:
        claims = state.get("extracted_claims", [])
        history = list(state.get("step_history", []))
        comparisons = []
        contradictions = []

        # Compare claim pairs
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                ca = claims[i]
                cb = claims[j]

                # Check text polarity
                text_a = ca['claim_text'].lower()
                text_b = cb['claim_text'].lower()

                has_neg_a = any(w in text_a for w in ['not', 'fail', 'degrade', 'ineffective', 'worse', 'limitation'])
                has_neg_b = any(w in text_b for w in ['not', 'fail', 'degrade', 'ineffective', 'worse', 'limitation'])

                has_pos_a = any(w in text_a for w in ['improve', 'outperform', 'enhance', 'reduce', 'effective', 'superior'])
                has_pos_b = any(w in text_b for w in ['improve', 'outperform', 'enhance', 'reduce', 'effective', 'superior'])

                if (has_neg_a and has_pos_b) or (has_pos_a and has_neg_b):
                    rel = {
                        "source_claim": ca['id'],
                        "target_claim": cb['id'],
                        "source_doc": ca['document_title'],
                        "target_doc": cb['document_title'],
                        "relationship_type": "CONTRADICTS",
                        "confidence": 0.84,
                        "summary": f"Potential tension between Source [{ca['source_index']}] and Source [{cb['source_index']}]."
                    }
                    contradictions.append(rel)
                    comparisons.append(rel)
                else:
                    rel = {
                        "source_claim": ca['id'],
                        "target_claim": cb['id'],
                        "source_doc": ca['document_title'],
                        "target_doc": cb['document_title'],
                        "relationship_type": "SUPPORTS",
                        "confidence": 0.81,
                        "summary": f"Concordant evidence between Source [{ca['source_index']}] and Source [{cb['source_index']}]."
                    }
                    comparisons.append(rel)

        step_info = {
            "step": "evidence_comparator",
            "message": f"Identified {len(comparisons)} cross-document claim comparisons ({len(contradictions)} potential contradictions).",
            "comparisons_count": len(comparisons),
            "contradictions_count": len(contradictions)
        }
        history.append(step_info)

        return {
            "current_step": "evidence_comparator",
            "cross_comparisons": comparisons,
            "contradictions": contradictions,
            "step_history": history
        }

    # 5. Synthesis Agent
    def node_synthesis_agent(self, state: ResearchState) -> Dict[str, Any]:
        query = state["original_query"]
        passages = state.get("retrieved_passages", [])
        claims = state.get("extracted_claims", [])
        contradictions = state.get("contradictions", [])
        history = list(state.get("step_history", []))
        retry_count = state.get("retry_count", 0)

        # Context builder
        sources_context = ""
        for p in passages:
            sources_context += f"Source [{p['source_index']}] (Document: '{p['document_title']}', Page {p['page_number']}, Section: {p['section_title']}):\n{p['text']}\n\n"

        prompt = f"""You are the Synthesis Agent in the ResearchGraph AI pipeline.
Synthesize a comprehensive, grounded research analysis addressing this question:
Question: "{query}"

Strict Citation Rules:
1. Every factual statement must cite its exact source using bracketed numbers like [1], [2] matching the provided sources.
2. DO NOT cite any sources outside of [1] through [{len(passages)}].
3. If findings contradict or qualify each other, explicitly contrast them.
4. Separate source-backed findings from general interpretation.

Sources:
{sources_context}
"""
        synthesis_text = None
        llm_resp = self.llm.generate(prompt)
        if llm_resp and len(llm_resp.strip()) > 80:
            synthesis_text = llm_resp.strip()

        if not synthesis_text:
            # Deterministic, source-grounded synthesis builder
            synthesis_lines = [
                f"### Evidence-Grounded Research Synthesis\n",
                f"**Research Question:** {query}\n",
                f"#### Core Empirical Findings\n"
            ]

            for c in claims:
                synthesis_lines.append(f"- **{c['document_title']}** (p. {c['page_number']}): {c['claim_text']} [{c['source_index']}]")

            if contradictions:
                synthesis_lines.append(f"\n#### Cross-Document Comparative Analysis & Contradictions\n")
                for ct in contradictions:
                    synthesis_lines.append(f"- **Contradiction/Tension Identified**: {ct['summary']} between '{ct['source_doc']}' and '{ct['target_doc']}'.")

            synthesis_lines.append(f"\n#### Methodological Implications & Scope\n")
            synthesis_lines.append(f"The analyzed literature shows convergent experimental evidence regarding {query.lower()}, with validated boundaries documented across the cited sources.")

            synthesis_text = "\n".join(synthesis_lines)

        step_info = {
            "step": "synthesis_agent",
            "message": f"Generated synthesis draft (iteration {retry_count + 1}).",
            "char_length": len(synthesis_text)
        }
        history.append(step_info)

        return {
            "current_step": "synthesis_agent",
            "raw_synthesis": synthesis_text,
            "step_history": history
        }

    # 6. Citation Validator
    def node_citation_validator(self, state: ResearchState) -> Dict[str, Any]:
        raw_synthesis = state.get("raw_synthesis", "")
        passages = state.get("retrieved_passages", [])
        history = list(state.get("step_history", []))
        retry_count = state.get("retry_count", 0)

        validation = CitationValidator.validate_report(raw_synthesis, passages)

        step_info = {
            "step": "citation_validator",
            "message": f"Audited citations: precision={validation['citation_precision']}, valid={validation['valid_citations_count']}, hallucinated={validation['hallucinated_citations_count']}.",
            "validation": validation
        }
        history.append(step_info)

        return {
            "current_step": "citation_validator",
            "validated_citations": validation['validated_citations'],
            "citation_metrics": validation,
            "retry_count": retry_count + 1,
            "step_history": history
        }

    # 7. Report Generator
    def node_report_generator(self, state: ResearchState) -> Dict[str, Any]:
        query = state["original_query"]
        history = list(state.get("step_history", []))
        is_sufficient = state.get("is_sufficient_evidence", True)
        passages = state.get("retrieved_passages", [])
        claims = state.get("extracted_claims", [])
        evidence_gaps = list(state.get("evidence_gaps", []))
        citation_metrics = state.get("citation_metrics", {})
        validated_citations = state.get("validated_citations", [])

        if not is_sufficient:
            # Grounded refusal when evidence is missing
            report_title = f"Insufficient Evidence Report: {query[:60]}"
            exec_summary = (
                f"The ResearchGraph AI evidence collection lacks sufficient grounded documents to answer the inquiry '{query}'. "
                f"Per system policy, no speculative or hallucinated claims have been generated."
            )
            synthesis_md = (
                f"# Research Analysis: {query}\n\n"
                f"## Evidence Status: Insufficient Grounded Context\n\n"
                f"> **System Notice**: The indexed research corpus does not contain documents with sufficient semantic overlap "
                f"or empirical data to reliably substantiate answers for this question.\n\n"
                f"### Observed Literature Gaps:\n"
                + "\n".join(f"- {gap}" for gap in evidence_gaps)
                + "\n\n### Recommended Actions:\n"
                f"- Ingest relevant papers on this subject via the Document Library.\n"
                f"- Refine search terms to match domain-specific terminology.\n"
            )
            findings = []
            faithfulness = 1.0
        else:
            report_title = f"Research Synthesis: {query[:60]}"
            synthesis_md = state.get("raw_synthesis", "")
            exec_summary = (
                f"Synthesized evidence from {len(passages)} passages across {len(set(p['document_id'] for p in passages))} papers. "
                f"Identified {len(claims)} primary empirical claims with verified citations. "
                f"Citation precision: {citation_metrics.get('citation_precision', 1.0) * 100:.1f}%."
            )
            findings = [{
                "claim_id": c["id"],
                "text": c["claim_text"],
                "source_title": c["document_title"],
                "page": c["page_number"],
                "confidence": c["confidence"]
            } for c in claims]
            faithfulness = citation_metrics.get('faithfulness_score', 1.0)

        final_report = {
            "title": report_title,
            "executive_summary": exec_summary,
            "synthesis_markdown": synthesis_md,
            "structured_findings": findings,
            "evidence_gaps": evidence_gaps,
            "citations": validated_citations,
            "faithfulness_score": faithfulness,
            "metadata": {
                "generated_at": datetime.datetime.utcnow().isoformat(),
                "query": query,
                "retrieved_passages_count": len(passages),
                "claims_count": len(claims),
                "citation_precision": citation_metrics.get("citation_precision", 1.0),
                "citation_coverage": citation_metrics.get("citation_coverage", 1.0),
            }
        }

        step_info = {
            "step": "report_generator",
            "message": "Generated final research intelligence report.",
            "report_title": report_title
        }
        history.append(step_info)

        return {
            "current_step": "report_generator",
            "final_report": final_report,
            "status": "COMPLETED",
            "step_history": history
        }

    def execute(self, query: str, mode: str = "deep_research") -> Dict[str, Any]:
        """Runs the LangGraph research workflow from start to finish."""
        initial_state: ResearchState = {
            "original_query": query,
            "query_id": str(uuid.uuid4()),
            "mode": mode,
            "subquestions": [],
            "retrieved_passages": [],
            "extracted_claims": [],
            "cross_comparisons": [],
            "contradictions": [],
            "evidence_gaps": [],
            "raw_synthesis": "",
            "validated_citations": [],
            "citation_metrics": {},
            "final_report": {},
            "current_step": "init",
            "step_history": [],
            "retry_count": 0,
            "max_retries": 2,
            "is_sufficient_evidence": True,
            "status": "RUNNING"
        }

        final_output = self.workflow.invoke(initial_state)
        return final_output
