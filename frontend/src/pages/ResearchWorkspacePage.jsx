import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function ResearchWorkspacePage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('deep_research');
  const [isRunning, setIsRunning] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [stepMessage, setStepMessage] = useState('');
  const [result, setResult] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [error, setError] = useState('');

  const STEPS = [
    { id: 'research_planner', title: '1. Planner' },
    { id: 'evidence_retriever', title: '2. Retriever' },
    { id: 'claim_extractor', title: '3. Claim Extractor' },
    { id: 'evidence_comparator', title: '4. Comparator' },
    { id: 'synthesis_agent', title: '5. Synthesizer' },
    { id: 'citation_validator', title: '6. Citation Validator' },
    { id: 'report_generator', title: '7. Report' },
  ];

  const sampleQuestions = [
    "How does GraphRAG improve over standard baseline RAG on global sensemaking questions?",
    "What are the latency and token cost trade-offs of knowledge graph indexing vs vector search?",
    "Does dense retrieval universally outperform sparse lexical search (BM25)?",
    "What mechanisms effectively mitigate factual hallucinations in scientific LLM synthesis?"
  ];

  const handleRun = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsRunning(true);
    setError('');
    setResult(null);
    setCurrentStepIndex(0);
    setStepMessage('Initializing research plan & decomposing subquestions...');

    // Simulate progressive stepping animation
    const stepInterval = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev < STEPS.length - 2) return prev + 1;
        return prev;
      });
    }, 900);

    try {
      const data = await api.runResearchWorkflow(query, mode);
      clearInterval(stepInterval);
      setCurrentStepIndex(STEPS.length - 1);
      setStepMessage('Research report compiled with validated citations.');
      setResult(data);
    } catch (err) {
      clearInterval(stepInterval);
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Research Workspace</h1>
          <p className="page-subtitle">
            Autonomous multi-agent grounded research synthesis powered by LangGraph, claim extraction, and mathematical citation verification.
          </p>
        </div>
      </div>

      {/* Query Input Card */}
      <div className="card" style={{ marginBottom: '28px' }}>
        <form onSubmit={handleRun}>
          <div style={{ marginBottom: '14px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Research Question or Hypothesis:
            </label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                className="input"
                style={{ fontSize: '1rem', padding: '12px 18px' }}
                placeholder="Ask an evidence-grounded research question across ingested papers..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isRunning}
                id="research-query-input"
              />
              <button
                type="submit"
                className="btn btn-primary"
                style={{ minWidth: '160px', fontSize: '0.95rem' }}
                disabled={isRunning || !query.trim()}
                id="run-research-btn"
              >
                {isRunning ? (
                  <>
                    <span className="spinner"></span> Synthesizing...
                  </>
                ) : (
                  <>Synthesize Evidence ➔</>
                )}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            {/* Quick sample chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Suggestions:</span>
              {sampleQuestions.map((sq, i) => (
                <button
                  key={i}
                  type="button"
                  className="badge badge-gray"
                  style={{ cursor: 'pointer', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
                  onClick={() => setQuery(sq)}
                >
                  {sq.substring(0, 42)}...
                </button>
              ))}
            </div>

            {/* Mode selection */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Workflow Mode:</span>
              <button
                type="button"
                className={`btn btn-sm ${mode === 'deep_research' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setMode('deep_research')}
              >
                7-Stage Multi-Agent
              </button>
              <button
                type="button"
                className={`btn btn-sm ${mode === 'quick_search' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setMode('quick_search')}
              >
                Quick Hybrid Search
              </button>
            </div>
          </div>
        </form>

        {/* Stepper when running or completed */}
        {(isRunning || result) && (
          <div style={{ marginTop: '28px', borderTop: '1px solid var(--border-subtle)', paddingTop: '20px' }}>
            <div className="agent-stepper">
              {STEPS.map((step, idx) => {
                const isActive = isRunning && currentStepIndex === idx;
                const isCompleted = currentStepIndex > idx || (!isRunning && result);
                return (
                  <div
                    key={step.id}
                    className={`agent-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                  >
                    <div className="agent-step-icon">
                      {isCompleted ? '✓' : idx + 1}
                    </div>
                    <div className="agent-step-title">{step.title}</div>
                  </div>
                );
              })}
            </div>

            {stepMessage && (
              <div style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--accent-cyan)', fontWeight: 500 }}>
                {isRunning && <span className="spinner" style={{ display: 'inline-block', width: 12, height: 12, marginRight: 8 }}></span>}
                {stepMessage}
              </div>
            )}
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fda4af', padding: '16px', borderRadius: '8px', marginBottom: '24px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Synthesis Results Display */}
      {result && result.report && (
        <div>
          {/* Executive Summary Card */}
          <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--accent-cyan)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span className="badge badge-cyan">Executive Synthesis</span>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <span className="badge badge-emerald">
                  Faithfulness: {(result.report.faithfulness_score * 100).toFixed(0)}%
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Latency: {result.latency_ms}ms
                </span>
              </div>
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ffffff', marginBottom: '10px' }}>
              {result.report.title}
            </h2>
            <p style={{ color: '#e2e8f0', fontSize: '1rem', lineHeight: 1.6 }}>
              {result.report.executive_summary}
            </p>
          </div>

          {/* Subquestions explored */}
          {result.subquestions && result.subquestions.length > 0 && (
            <div className="card" style={{ marginBottom: '24px', background: 'rgba(15, 23, 42, 0.45)' }}>
              <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--accent-violet)', fontWeight: 700, marginBottom: '8px' }}>
                Agent 1 (Planner) Decomposed Subquestions:
              </div>
              <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                {result.subquestions.map((sq, i) => (
                  <li key={i} style={{ marginBottom: '4px' }}>{sq}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Structured Empirical Claims */}
          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
              Verified Empirical Claims & Attributions ({result.extracted_claims.length})
            </h3>
            <div className="grid-2">
              {result.extracted_claims.map((claim, idx) => (
                <div key={idx} className="card" style={{ padding: '18px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span className="badge badge-violet">{claim.id}</span>
                    <button
                      className="citation-pill"
                      onClick={() => setSelectedEvidence({
                        document_title: claim.document_title,
                        page_number: claim.page_number,
                        section_title: claim.section_title,
                        source_excerpt: claim.supporting_passage,
                        score: claim.confidence
                      })}
                    >
                      [{claim.source_index}] Source p.{claim.page_number}
                    </button>
                  </div>
                  <div style={{ fontWeight: 600, color: '#f1f5f9', marginBottom: '8px', fontSize: '0.92rem' }}>
                    {claim.claim_text}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    From: {claim.document_title}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Contradictions & Tensions (if detected) */}
          {result.contradictions && result.contradictions.length > 0 && (
            <div className="card" style={{ marginBottom: '24px', border: '1px solid rgba(244, 63, 94, 0.4)', background: 'rgba(244, 63, 94, 0.05)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span className="badge badge-rose">Opposing Evidence Detected</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Cross-Document Tension</span>
              </div>
              {result.contradictions.map((ct, idx) => (
                <div key={idx} style={{ padding: '10px 0', borderBottom: idx < result.contradictions.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                  <div style={{ fontWeight: 600, color: '#fda4af', fontSize: '0.92rem' }}>
                    {ct.summary}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Between: '{ct.source_doc}' and '{ct.target_doc}'
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Full Report Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
            <button
              className="btn btn-secondary"
              onClick={() => navigate('/contradictions')}
            >
              Review Contradictions Queue
            </button>
            <a
              className="btn btn-primary"
              href={`/api/agents/reports/${result.report_id}/export/?format=markdown`}
              download
            >
              Export Report (Markdown) ⬇
            </a>
          </div>
        </div>
      )}

      <EvidenceDrawer
        evidence={selectedEvidence}
        isOpen={Boolean(selectedEvidence)}
        onClose={() => setSelectedEvidence(null)}
      />
    </div>
  );
}
