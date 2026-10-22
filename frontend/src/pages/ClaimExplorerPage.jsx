import React, { useState, useEffect } from 'react';
import { api } from '../api';
import ReviewModal from '../components/ReviewModal';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function ClaimExplorerPage() {
  const [claims, setClaims] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [minConfidence, setMinConfidence] = useState(0.7);
  const [isLoading, setIsLoading] = useState(true);
  const [reviewingClaim, setReviewingClaim] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [claimsRes, docsRes] = await Promise.all([
        api.getClaims({
          document_id: selectedDocId,
          review_status: selectedStatus,
          min_confidence: minConfidence
        }),
        api.getDocuments()
      ]);
      setClaims(claimsRes.claims || []);
      setDocuments(docsRes.documents || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedDocId, selectedStatus, minConfidence]);

  const handleReviewSubmit = async ({ id, decision, notes }) => {
    await api.reviewClaim(id, decision, notes);
    setSuccessMsg(`Claim ${id} successfully updated with decision: ${decision}`);
    loadData();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'ACCEPTED': return <span className="badge badge-emerald">✓ Accepted</span>;
      case 'REJECTED': return <span className="badge badge-rose">✕ Rejected</span>;
      case 'FLAGGED': return <span className="badge badge-amber">! Flagged</span>;
      default: return <span className="badge badge-gray">Unreviewed</span>;
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Factual Claim Explorer</h1>
          <p className="page-subtitle">
            Explore structured assertions extracted from literature passages, inspect supporting source evidence, and record human review decisions.
          </p>
        </div>
      </div>

      {successMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#6ee7b7', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
          ✓ {successMsg}
        </div>
      )}

      {/* Filters Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: '220px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Document:</label>
            <select
              className="select"
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              id="claim-filter-doc"
            >
              <option value="">All Documents</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.title}</option>
              ))}
            </select>
          </div>

          <div style={{ width: '180px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Review Status:</label>
            <select
              className="select"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              id="claim-filter-status"
            >
              <option value="">All Statuses</option>
              <option value="UNREVIEWED">Unreviewed</option>
              <option value="ACCEPTED">Accepted</option>
              <option value="FLAGGED">Flagged for Review</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>

          <div style={{ width: '160px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Min Confidence ({minConfidence}):</label>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
            />
          </div>
        </div>
      </div>

      {/* Claims List */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <span style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
            Extracted Claims ({claims.length})
          </span>
        </div>

        {isLoading ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
            <div className="spinner" style={{ margin: '0 auto 8px auto' }}></div>
            Loading claims...
          </div>
        ) : claims.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No claims matched your filter criteria.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {claims.map((claim) => (
              <div key={claim.id} className="card" style={{ padding: '20px' }} id={`claim-card-${claim.id}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="badge badge-violet">{claim.id}</span>
                    {getStatusBadge(claim.review_status)}
                    <span className="badge badge-cyan">Page {claim.page_number}</span>
                    <span className="badge badge-emerald">Conf: {(claim.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setReviewingClaim(claim)}
                    id={`review-claim-btn-${claim.id}`}
                  >
                    Review Claim
                  </button>
                </div>

                <div style={{ fontSize: '1rem', fontWeight: 600, color: '#ffffff', marginBottom: '10px' }}>
                  {claim.claim_text}
                </div>

                {/* Supporting passage box */}
                <div style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
                  <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 600 }}>
                    Supporting Source Excerpt:
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#cbd5e1', fontStyle: 'italic', lineHeight: 1.5 }}>
                    "{claim.supporting_passage}"
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <span>Source: <b>{claim.document_title}</b></span>
                  <button
                    style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer', fontSize: '0.8rem' }}
                    onClick={() => setSelectedEvidence({
                      document_title: claim.document_title,
                      page_number: claim.page_number,
                      section_title: claim.section_title,
                      text: claim.supporting_passage,
                      score: claim.confidence
                    })}
                  >
                    View Passage Provenance ➔
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <ReviewModal
        item={reviewingClaim}
        type="claim"
        isOpen={Boolean(reviewingClaim)}
        onClose={() => setReviewingClaim(null)}
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
