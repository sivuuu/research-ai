import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function ResearchReportPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await api.getResearchHistory();
      const queries = data.queries || [];
      setHistory(queries);

      // Select first report or find by param
      if (queries.length > 0) {
        const found = id ? queries.find(q => q.reports?.[0]?.id === id) : queries[0];
        if (found && found.reports?.length > 0) {
          setSelectedReport(found.reports[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [id]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Research Intelligence Reports</h1>
          <p className="page-subtitle">
            Exportable, audit-ready research syntheses with verified citation provenance, explicit evidence bounds, and mathematical faithfulness tracking.
          </p>
        </div>
      </div>

      <div className="grid-4" style={{ gridTemplateColumns: '300px 1fr', gap: '24px' }}>
        {/* Left: Report History Sidebar */}
        <div>
          <div className="card" style={{ padding: '16px' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
              Past Syntheses ({history.length})
            </h3>
            {isLoading ? (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <div className="spinner"></div>
              </div>
            ) : history.length === 0 ? (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                No reports generated yet. Run a synthesis from the Workspace.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '600px', overflowY: 'auto' }}>
                {history.map((q) => {
                  const rep = q.reports?.[0];
                  if (!rep) return null;
                  const isSelected = selectedReport?.id === rep.id;
                  return (
                    <div
                      key={q.id}
                      className={`card card-clickable ${isSelected ? 'active' : ''}`}
                      style={{
                        padding: '12px',
                        background: isSelected ? 'rgba(56, 189, 248, 0.12)' : 'rgba(0,0,0,0.25)',
                        border: isSelected ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)'
                      }}
                      onClick={() => setSelectedReport(rep)}
                    >
                      <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.85rem', marginBottom: '4px' }}>
                        {rep.title.substring(0, 36)}...
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {new Date(rep.created_at).toLocaleDateString()} • Faithfulness: {(rep.faithfulness_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Full Report View */}
        <div>
          {selectedReport ? (
            <div className="card" style={{ padding: '32px' }} id="full-research-report">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '20px', marginBottom: '24px' }}>
                <div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
                    <span className="badge badge-cyan">Research Intelligence Report</span>
                    <span className="badge badge-emerald">Faithfulness: {(selectedReport.faithfulness_score * 100).toFixed(0)}%</span>
                  </div>
                  <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ffffff' }}>
                    {selectedReport.title}
                  </h2>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <a
                    className="btn btn-secondary btn-sm"
                    href={`/api/agents/reports/${selectedReport.id}/export/?format=html`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Export HTML
                  </a>
                  <a
                    className="btn btn-primary btn-sm"
                    href={`/api/agents/reports/${selectedReport.id}/export/?format=markdown`}
                    download
                  >
                    Export Markdown ⬇
                  </a>
                </div>
              </div>

              {/* Executive Summary */}
              <div style={{ background: 'rgba(56, 189, 248, 0.05)', borderLeft: '4px solid var(--accent-cyan)', padding: '18px', borderRadius: '4px', marginBottom: '28px' }}>
                <h4 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '6px' }}>
                  Executive Summary
                </h4>
                <p style={{ color: '#e2e8f0', fontSize: '0.98rem', lineHeight: 1.6 }}>
                  {selectedReport.executive_summary}
                </p>
              </div>

              {/* Report Body */}
              <div style={{ color: '#cbd5e1', fontSize: '0.95rem', lineHeight: 1.7, marginBottom: '32px', whiteSpace: 'pre-wrap' }}>
                {selectedReport.synthesis_markdown}
              </div>

              {/* Evidence Gaps & Limitations */}
              {selectedReport.evidence_gaps && selectedReport.evidence_gaps.length > 0 && (
                <div style={{ background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '8px', padding: '18px', marginBottom: '32px' }}>
                  <h4 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--accent-amber)', fontWeight: 700, marginBottom: '8px' }}>
                    Identified Evidence Gaps & Corpus Limitations
                  </h4>
                  <ul style={{ paddingLeft: '20px', color: '#fef3c7', fontSize: '0.9rem' }}>
                    {selectedReport.evidence_gaps.map((gap, i) => (
                      <li key={i} style={{ marginBottom: '6px' }}>{gap}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Validated Citations Table */}
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
                  Traceable Citation Provenance Table ({selectedReport.citations?.length || 0})
                </h3>
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Ref</th>
                        <th>Document & Author</th>
                        <th>Page</th>
                        <th>Exact Supporting Excerpt</th>
                        <th>Status</th>
                        <th>Inspect</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedReport.citations || []).map((c, idx) => (
                        <tr key={idx}>
                          <td><b>[{idx + 1}]</b></td>
                          <td style={{ fontWeight: 600, color: '#ffffff' }}>
                            {c.document_title}
                          </td>
                          <td><span className="badge badge-cyan">Page {c.page_number}</span></td>
                          <td style={{ fontSize: '0.82rem', color: '#cbd5e1', maxWidth: '380px' }}>
                            "{c.source_excerpt}"
                          </td>
                          <td>
                            <span className={`badge ${c.is_valid ? 'badge-emerald' : 'badge-rose'}`}>
                              {c.status || 'VALID'}
                            </span>
                          </td>
                          <td>
                            <button
                              className="citation-pill"
                              onClick={() => setSelectedEvidence(c)}
                            >
                              Inspect ➔
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
              Select a research report from the sidebar or generate one in the Workspace.
            </div>
          )}
        </div>
      </div>

      <EvidenceDrawer
        evidence={selectedEvidence}
        isOpen={Boolean(selectedEvidence)}
        onClose={() => setSelectedEvidence(null)}
      />
    </div>
  );
}
