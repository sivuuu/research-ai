import React, { useState, useEffect } from 'react';
import { api } from '../api';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function SearchResultsPage() {
  const [query, setQuery] = useState('GraphRAG community summarization global questions');
  const [method, setMethod] = useState('hybrid');
  const [rerank, setRerank] = useState(true);
  const [topK, setTopK] = useState(6);
  const [minScore, setMinScore] = useState(0.15);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const data = await api.search({
        query,
        method,
        rerank,
        top_k: topK,
        min_score: minScore
      });
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  // Simple query term highlighter
  const highlightTerms = (text, q) => {
    if (!q) return text;
    const terms = q.toLowerCase().split(/\s+/).filter(t => t.length > 2);
    if (!terms.length) return text;

    const regex = new RegExp(`(${terms.join('|')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, i) =>
      terms.includes(part.toLowerCase()) ? (
        <mark key={i} style={{ background: 'rgba(56, 189, 248, 0.35)', color: '#ffffff', padding: '1px 3px', borderRadius: '3px' }}>
          {part}
        </mark>
      ) : part
    );
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Evidence Retrieval Playground</h1>
          <p className="page-subtitle">
            Perform dense semantic vector, sparse lexical, or RRF hybrid search over chunks with term highlighting and provenance offsets.
          </p>
        </div>
      </div>

      {/* Search Controls Card */}
      <div className="card" style={{ marginBottom: '28px' }}>
        <form onSubmit={handleSearch}>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
            <input
              type="text"
              className="input"
              style={{ fontSize: '1rem', padding: '12px 18px' }}
              placeholder="Search concepts, technical jargon, or empirical questions..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              id="search-input"
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading || !query.trim()}
              id="search-btn"
              style={{ minWidth: '130px' }}
            >
              {isLoading ? <span className="spinner"></span> : 'Search'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Method:</span>
              <select
                className="select"
                style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                id="search-method-select"
              >
                <option value="hybrid">Hybrid (Dense Vector + BM25 RRF)</option>
                <option value="vector">Dense Vector Search (Cosine)</option>
                <option value="lexical">Sparse Lexical Search</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={rerank}
                  onChange={(e) => setRerank(e.target.checked)}
                  id="rerank-checkbox"
                />
                <span>Enable Reranker</span>
              </label>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Top K:</span>
              <select
                className="select"
                style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={8}>8</option>
                <option value={12}>12</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Min Score:</span>
              <input
                type="range"
                min="0.05"
                max="0.8"
                step="0.05"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
              />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', minWidth: '35px' }}>
                {minScore}
              </span>
            </div>
          </div>
        </form>
      </div>

      {error && (
        <div style={{ background: 'rgba(244, 63, 94, 0.15)', color: '#fda4af', padding: '14px', borderRadius: '8px', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Results List */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
            Retrieved Evidence Passages ({results.length})
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Ranked by {method} {rerank ? '+ density reranking' : ''}
          </span>
        </div>

        {results.length === 0 && !isLoading ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No passages matched the query with the current filters and minimum score threshold ({minScore}).
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {results.map((res) => (
              <div
                key={res.chunk_id}
                className="card card-clickable"
                style={{ padding: '20px' }}
                onClick={() => setSelectedEvidence(res)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="badge badge-cyan">Rank #{res.rank}</span>
                    <span className="badge badge-emerald">Score: {(res.score * 100).toFixed(1)}%</span>
                    <span style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.95rem' }}>
                      {res.document_title}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span className="badge badge-gray">Page {res.page_number}</span>
                    {res.section_title && (
                      <span className="badge badge-violet">§ {res.section_title}</span>
                    )}
                  </div>
                </div>

                <div style={{ fontSize: '0.92rem', color: '#e2e8f0', lineHeight: 1.6, marginBottom: '12px' }}>
                  {highlightTerms(res.text, query)}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                  <span>Method: {res.retrieval_method}</span>
                  <span>Offsets: [{res.start_char}..{res.end_char}]</span>
                  <span style={{ color: 'var(--accent-cyan)' }}>Click to inspect provenance ➔</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <EvidenceDrawer
        evidence={selectedEvidence}
        isOpen={Boolean(selectedEvidence)}
        onClose={() => setSelectedEvidence(null)}
      />
    </div>
  );
}
