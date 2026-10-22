import React, { useState } from 'react';

export default function ReviewModal({ item, type = 'claim', isOpen, onClose, onSubmitted }) {
  const [decision, setDecision] = useState('ACCEPT');
  const [notes, setNotes] = useState('');
  const [correctedType, setCorrectedType] = useState('QUALIFIES');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen || !item) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onSubmitted({
        id: item.id,
        decision,
        notes,
        corrected_type: decision === 'MODIFY' ? correctedType : null,
      });
      onClose();
    } catch (err) {
      alert(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} id="review-modal-backdrop">
      <div className="modal-content" onClick={(e) => e.stopPropagation()} id="review-modal">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>
            {type === 'claim' ? 'Review Extracted Claim' : 'Review Inter-Paper Relationship'}
          </h3>
          <button className="btn btn-secondary btn-sm" onClick={onClose} style={{ padding: '2px 8px' }}>✕</button>
        </div>

        {type === 'claim' ? (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Claim Text:</div>
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', fontSize: '0.9rem', marginBottom: '10px' }}>
              {item.claim_text}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Supporting Source Passage:</div>
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              "{item.supporting_passage}"
            </div>
          </div>
        ) : (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <span className={`badge ${item.relationship_type === 'CONTRADICTS' ? 'badge-rose' : 'badge-emerald'}`}>
                {item.relationship_type}
              </span>
              <span className="badge badge-gray">Confidence: {(item.confidence * 100).toFixed(0)}%</span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              {item.evidence_summary}
            </div>
            <div className="grid-2" style={{ gap: '12px', marginBottom: '12px' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '6px', fontSize: '0.8rem' }}>
                <div style={{ color: 'var(--accent-cyan)', fontWeight: 600, marginBottom: '4px' }}>Source Assertion:</div>
                "{item.source_claim_text}"
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '6px', fontSize: '0.8rem' }}>
                <div style={{ color: 'var(--accent-rose)', fontWeight: 600, marginBottom: '4px' }}>Target Assertion:</div>
                "{item.target_claim_text}"
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', fontWeight: 600 }}>
              Decision Action:
            </label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className={`btn btn-sm ${decision === 'ACCEPT' ? 'btn-success' : 'btn-secondary'}`}
                onClick={() => setDecision('ACCEPT')}
                id="decision-accept-btn"
              >
                ✓ Accept
              </button>
              <button
                type="button"
                className={`btn btn-sm ${decision === 'REJECT' ? 'btn-danger' : 'btn-secondary'}`}
                onClick={() => setDecision('REJECT')}
                id="decision-reject-btn"
              >
                ✕ Reject
              </button>
              {type === 'relationship' && (
                <button
                  type="button"
                  className={`btn btn-sm ${decision === 'MODIFY' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setDecision('MODIFY')}
                  id="decision-modify-btn"
                >
                  ✎ Modify Type
                </button>
              )}
            </div>
          </div>

          {type === 'relationship' && decision === 'MODIFY' && (
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 600 }}>
                Corrected Relationship Type:
              </label>
              <select
                className="select"
                value={correctedType}
                onChange={(e) => setCorrectedType(e.target.value)}
                id="corrected-type-select"
              >
                <option value="QUALIFIES">QUALIFIES (Adds boundary conditions or constraints)</option>
                <option value="SUPPORTS">SUPPORTS (Concordant evidence)</option>
                <option value="DEPENDS_ON">DEPENDS ON (Methodological prerequisite)</option>
                <option value="DERIVED_FROM">DERIVED FROM (Extension of foundation)</option>
                <option value="CONTRADICTS">CONTRADICTS (Opposing empirical finding)</option>
              </select>
            </div>
          )}

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 600 }}>
              Reviewer Rationale & Notes (Optional):
            </label>
            <textarea
              className="textarea"
              rows="3"
              placeholder="e.g. Verified opposing sample sizes and methodologies..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              id="reviewer-notes-input"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting} id="submit-review-btn">
              {isSubmitting ? 'Recording...' : 'Record Decision'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
