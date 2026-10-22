import React, { useState, useEffect } from 'react';
import { api } from '../api';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function ComparisonMatrixPage() {
  const [matrixData, setMatrixData] = useState({ documents: [], matrix: [] });
  const [topicFilter, setTopicFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  const loadMatrix = async () => {
    setIsLoading(true);
    try {
      const data = await api.getComparisonMatrix([], topicFilter);
      setMatrixData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMatrix();
  }, [topicFilter]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Cross-Paper Comparison Matrix</h1>
          <p className="page-subtitle">
            Side-by-side empirical comparison across research papers, highlighting areas of convergence, boundary conditions, and direct disagreements.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ padding: '14px 20px', marginBottom: '24px', display: 'flex', gap: '16px', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Filter by Topic / Variable:</span>
        <input
          type="text"
          className="input"
          style={{ maxWidth: '320px', padding: '6px 12px', fontSize: '0.85rem' }}
          placeholder="e.g. Hallucination, Latency, BM25, Graph..."
          value={topicFilter}
          onChange={(e) => setTopicFilter(e.target.value)}
          id="matrix-topic-input"
        />
        {topicFilter && (
          <button className="btn btn-secondary btn-sm" onClick={() => setTopicFilter('')}>
            Clear
          </button>
        )}
      </div>

      {/* Matrix Table */}
      {isLoading ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner" style={{ margin: '0 auto 8px auto' }}></div>
          Computing cross-paper comparison matrix...
        </div>
      ) : matrixData.documents.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          No ingested documents available for comparison. Please ingest papers via the Document Library.
        </div>
      ) : (
        <div className="table-container" style={{ maxHeight: '70vh' }}>
          <table className="table" id="comparison-matrix-table">
            <thead>
              <tr>
                <th style={{ width: '220px', position: 'sticky', left: 0, zIndex: 10, background: '#0e1424' }}>
                  Research Variable / Subject
                </th>
                {matrixData.documents.map((doc) => (
                  <th key={doc.id} style={{ minWidth: '320px', maxWidth: '400px' }}>
                    <div style={{ fontWeight: 700, color: '#ffffff' }}>{doc.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {doc.claims_count} documented claims
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrixData.matrix.map((row, rIdx) => (
                <tr key={rIdx}>
                  <td style={{ position: 'sticky', left: 0, zIndex: 5, background: '#0d121f', fontWeight: 600, color: 'var(--accent-cyan)', borderRight: '1px solid var(--border-subtle)' }}>
                    {row.topic_or_entity}
                  </td>
                  {row.cells.map((cell, cIdx) => (
                    <td key={cIdx} style={{ verticalAlign: 'top', background: cell.has_evidence ? 'rgba(255,255,255,0.01)' : 'rgba(0,0,0,0.1)' }}>
                      {cell.has_evidence ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {cell.claims.map((cl, i) => (
                            <div
                              key={i}
                              style={{
                                background: 'rgba(0,0,0,0.3)',
                                border: '1px solid var(--border-subtle)',
                                borderRadius: '6px',
                                padding: '10px',
                                fontSize: '0.84rem'
                              }}
                            >
                              <div style={{ color: '#f1f5f9', marginBottom: '6px' }}>
                                {cl.text}
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span className="badge badge-gray" style={{ fontSize: '0.7rem' }}>Page {cl.page}</span>
                                <button
                                  className="citation-pill"
                                  onClick={() => setSelectedEvidence({
                                    document_title: cell.document_title,
                                    page_number: cl.page,
                                    text: cl.text,
                                    score: cl.confidence
                                  })}
                                >
                                  Inspect Provenance ➔
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                          No explicit assertion in this document
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
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
