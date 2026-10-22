import React, { useState, useEffect } from 'react';
import { api } from '../api';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function DocumentLibraryPage() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedDocDetails, setSelectedDocDetails] = useState(null);
  const [selectedChunk, setSelectedChunk] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      const res = await api.getDocuments(statusFilter);
      setDocuments(res.documents || []);
      setErrorMessage('');
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [statusFilter]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const res = await api.uploadDocument(file);
      setSuccessMessage(`Document '${file.name}' successfully uploaded and ingested!`);
      loadDocuments();
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (docId, title) => {
    if (!window.confirm(`Permanently delete '${title}' and all derived chunks, embeddings, and claims?`)) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      setSuccessMessage(`Document '${title}' and derived records deleted.`);
      loadDocuments();
      if (selectedDocDetails?.document?.id === docId) {
        setSelectedDocDetails(null);
      }
    } catch (err) {
      setErrorMessage(err.message);
    }
  };

  const handleInspectDoc = async (docId) => {
    try {
      const details = await api.getDocument(docId);
      setSelectedDocDetails(details);
    } catch (err) {
      setErrorMessage(err.message);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="badge badge-emerald">● Ingested</span>;
      case 'FAILED':
        return <span className="badge badge-rose">✕ Failed</span>;
      case 'PARSING':
      case 'EMBEDDING':
      case 'EXTRACTING_CLAIMS':
        return <span className="badge badge-amber"><span className="spinner" style={{ width: 10, height: 10 }}></span> {status}</span>;
      default:
        return <span className="badge badge-gray">{status}</span>;
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Research Document Library</h1>
          <p className="page-subtitle">
            Ingest, parse, and monitor research literature with automatic chunk offset tracking and SHA-256 provenance deduplication.
          </p>
        </div>
        <div>
          <label className="btn btn-primary" style={{ cursor: isUploading ? 'not-allowed' : 'pointer' }}>
            {isUploading ? (
              <>
                <span className="spinner" style={{ width: 14, height: 14 }}></span> Ingesting...
              </>
            ) : (
              <>+ Ingest Research Document</>
            )}
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
              disabled={isUploading}
              style={{ display: 'none' }}
              id="upload-document-input"
            />
          </label>
        </div>
      </div>

      {errorMessage && (
        <div style={{ background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#fda4af', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
          ⚠️ {errorMessage}
        </div>
      )}

      {successMessage && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#6ee7b7', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
          ✓ {successMessage}
        </div>
      )}

      {/* Stats bar */}
      <div className="grid-4" style={{ marginBottom: '24px' }}>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Indexed Documents</div>
          <div style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{documents.length}</div>
        </div>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Passages / Chunks</div>
          <div style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
            {documents.reduce((acc, d) => acc + (d.chunks_count || 0), 0)}
          </div>
        </div>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Extracted Factual Claims</div>
          <div style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--accent-violet)' }}>
            {documents.reduce((acc, d) => acc + (d.claims_count || 0), 0)}
          </div>
        </div>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Ingestion Reliability</div>
          <div style={{ fontSize: '1.7rem', fontWeight: 800, color: '#ffffff' }}>
            {documents.length ? `${((documents.filter(d => d.ingestion_status === 'COMPLETED').length / documents.length) * 100).toFixed(0)}%` : '100%'}
          </div>
        </div>
      </div>

      {/* Document table */}
      <div className="table-container">
        <table className="table" id="documents-table">
          <thead>
            <tr>
              <th>Title & File</th>
              <th>Authors</th>
              <th>Status</th>
              <th>Pages</th>
              <th>Chunks</th>
              <th>Claims</th>
              <th>SHA-256 Hash</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '32px' }}>
                  <div className="spinner" style={{ margin: '0 auto 8px auto' }}></div>
                  Loading indexed collection...
                </td>
              </tr>
            ) : documents.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No documents found. Use the "+ Ingest Research Document" button to add PDF, TXT, or MD files.
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: '#ffffff' }}>{doc.title}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{doc.file_name}</div>
                  </td>
                  <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    {doc.authors && doc.authors.length > 0 ? doc.authors.slice(0, 2).join(', ') + (doc.authors.length > 2 ? ' et al.' : '') : <span style={{ color: 'var(--text-muted)' }}>Not specified</span>}
                  </td>
                  <td>{getStatusBadge(doc.ingestion_status)}</td>
                  <td>{doc.total_pages}</td>
                  <td><span className="badge badge-gray">{doc.chunks_count || 0}</span></td>
                  <td><span className="badge badge-violet">{doc.claims_count || 0}</span></td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {(doc.file_hash || '').substring(0, 10)}...
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleInspectDoc(doc.id)}
                        id={`inspect-doc-${doc.id}`}
                      >
                        Inspect
                      </button>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(doc.id, doc.title)}
                        id={`delete-doc-${doc.id}`}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Selected document passage inspector */}
      {selectedDocDetails && (
        <div className="card" style={{ marginTop: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>
                Chunk Inspection: {selectedDocDetails.document.title}
              </h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {selectedDocDetails.chunks.length} extracted passages preserving page offsets and section bounds
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => setSelectedDocDetails(null)}>
              Close Panel
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px', maxHeight: '420px', overflowY: 'auto' }}>
            {selectedDocDetails.chunks.map((chk) => (
              <div
                key={chk.id}
                className="card card-clickable"
                style={{ padding: '14px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)' }}
                onClick={() => setSelectedChunk({ ...chk, document_title: selectedDocDetails.document.title })}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span className="badge badge-cyan">Page {chk.page_number}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Chunk #{chk.chunk_index}</span>
                </div>
                {chk.section_title && (
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '6px' }}>
                    § {chk.section_title}
                  </div>
                )}
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {chk.text}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <EvidenceDrawer
        evidence={selectedChunk}
        isOpen={Boolean(selectedChunk)}
        onClose={() => setSelectedChunk(null)}
      />
    </div>
  );
}
