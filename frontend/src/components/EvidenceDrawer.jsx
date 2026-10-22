import React from 'react';

export default function EvidenceDrawer({ evidence, isOpen, onClose }) {
  if (!isOpen || !evidence) return null;

  return (
    <>
      <div className="modal-overlay" onClick={onClose} style={{ zIndex: 240 }} />
      <div className={`drawer ${isOpen ? 'open' : ''}`} id="evidence-drawer">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-cyan">Source Provenance</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Page {evidence.page_number || 1}</span>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            onClick={onClose}
            id="close-drawer-btn"
            style={{ padding: '4px 8px' }}
          >
            ✕
          </button>
        </div>

        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '8px', color: '#ffffff' }}>
          {evidence.document_title || evidence.doc_title || 'Source Document'}
        </h3>

        {evidence.section_title && (
          <div style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginBottom: '16px' }}>
            § {evidence.section_title}
          </div>
        )}

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
          <span className="badge badge-gray">ID: {(evidence.chunk_id || evidence.id || '').substring(0, 13)}...</span>
          {evidence.score !== undefined && (
            <span className="badge badge-emerald">Relevance: {(evidence.score * 100).toFixed(1)}%</span>
          )}
          {evidence.start_char !== undefined && (
            <span className="badge badge-violet">Offsets: [{evidence.start_char}..{evidence.end_char}]</span>
          )}
        </div>

        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>
            Exact Supporting Passage Excerpt
          </div>
          <div style={{
            background: 'rgba(0, 0, 0, 0.4)',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            fontSize: '0.9rem',
            lineHeight: 1.6,
            color: '#e2e8f0',
            fontFamily: 'inherit',
            whiteSpace: 'pre-wrap'
          }}>
            {evidence.text || evidence.source_excerpt || evidence.supporting_passage || 'No excerpt available.'}
          </div>
        </div>

        {evidence.subquestion && (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 600 }}>
              Addressed Subquestion
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              {evidence.subquestion}
            </div>
          </div>
        )}

        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </>
  );
}
