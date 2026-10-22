import React, { useState, useEffect } from 'react';
import { api } from '../api';
import ReviewModal from '../components/ReviewModal';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function ContradictionQueuePage() {
  const [contradictions, setContradictions] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [reviewingRel, setReviewingRel] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');

  const loadQueue = async () => {
    setIsLoading(true);
    try {
      const data = await api.getContradictions(statusFilter);
      setContradictions(data.contradictions || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [statusFilter]);

  const handleReviewSubmit = async ({ id, decision, notes, corrected_type }) => {
    await api.reviewRelationship(id, decision, notes, corrected_type);
    setSuccessMsg(`Decision '${decision}' successfully applied to relationship.`);
    loadQueue();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACCEPTED':
        return <span className="badge badge-emerald">✓ Verified Contradiction</span>;
      case 'REJECTED':
        return <span className="badge badge-rose">✕ Rejected (False Positive)</span>;
      case 'FLAGGED_FOR_HUMAN_REVIEW':
        return <span className="badge badge-amber">! Flagged for Review</span>;
      default:
        return <span className="badge badge-gray">{status}</span>;
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Contradiction & Evidence Review Queue</h1>
          <p className="page-subtitle">
            Audit empirical tensions and conflicting scientific conclusions across papers with human-in-the-loop review actions.
          </p>
        </div>
      </div>

      {successMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#6ee7b7', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
          ✓ {successMsg}
        </div>
      )}

      {/* Queue Filter */}
      <div className="card" style={{ padding: '14px 20px', marginBottom: '24px', display: 'flex', gap: '16px', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Status Filter:</span>
        <select
          className="select"
          style={{ width: 'auto', padding: '6px 14px', fontSize: '0.85rem' }}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          id="contradiction-status-filter"
        >
          <option value="">All Items</option>
          <option value="FLAGGED_FOR_HUMAN_REVIEW">Flagged for Review</option>
          <option value="ACCEPTED">Accepted Contradictions</option>
          <option value="REJECTED">Rejected False Positives</option>
        </select>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {contradictions.length} detected contradictions in queue
        </span>
      </div>

      {/* Contradiction Cards */}
      {isLoading ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner" style={{ margin: '0 auto 8px auto' }}></div>
          Loading contradiction queue...
        </div>
      ) : contradictions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          No contradictions currently in the queue with the selected filter.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {contradictions.map((item) => (
            <div key={item.id} className="card" style={{ borderLeft: '4px solid var(--accent-rose)' }} id={`contradiction-card-${item.id}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="badge badge-rose">CONTRADICTION</span>
                  {getStatusBadge(item.status)}
                  <span className="badge badge-gray">Confidence: {(item.confidence * 100).toFixed(0)}%</span>
                </div>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setReviewingRel(item)}
                  id={`review-rel-btn-${item.id}`}
                >
                  ✎ Review Decision
                </button>
              </div>

              {/* Evidence explanation summary */}
              <div style={{ background: 'rgba(244, 63, 94, 0.08)', border: '1px solid rgba(244, 63, 94, 0.2)', borderRadius: '8px', padding: '12px 16px', marginBottom: '16px', color: '#fda4af', fontSize: '0.9rem' }}>
                <b>Stance Analysis:</b> {item.evidence_summary}
              </div>

              {/* Side-by-side claim comparison */}
              <div className="grid-2" style={{ gap: '16px' }}>
                {/* Paper A */}
                <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>
                      Paper A: {item.source_doc_title}
                    </span>
                    <button
                      className="citation-pill"
                      onClick={() => setSelectedEvidence({
                        document_title: item.source_doc_title,
                        text: item.source_passage || item.source_claim_text,
                      })}
                    >
                      Inspect Source ➔
                    </button>
                  </div>
                  <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: '0.95rem', marginBottom: '10px' }}>
                    "{item.source_claim_text}"
                  </div>
                  {item.source_passage && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px' }}>
                      Context: "{item.source_passage.substring(0, 180)}..."
                    </div>
                  )}
                </div>

                {/* Paper B */}
                <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--accent-rose)', fontWeight: 700 }}>
                      Paper B: {item.target_doc_title}
                    </span>
                    <button
                      className="citation-pill"
                      onClick={() => setSelectedEvidence({
                        document_title: item.target_doc_title,
                        text: item.target_passage || item.target_claim_text,
                      })}
                    >
                      Inspect Source ➔
                    </button>
                  </div>
                  <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: '0.95rem', marginBottom: '10px' }}>
                    "{item.target_claim_text}"
                  </div>
                  {item.target_passage && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px' }}>
                      Context: "{item.target_passage.substring(0, 180)}..."
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <ReviewModal
        item={reviewingRel}
        type="relationship"
        isOpen={Boolean(reviewingRel)}
        onClose={() => setReviewingRel(null)}
        onSubmitted={handleReviewSubmit}
      />

      <EvidenceDrawer
        evidence={selectedEvidence}
        isOpen={Boolean(selectedEvidence)}
        onClose={() => setSelectedEvidence(null)}
      />
    </div>
  );
}
