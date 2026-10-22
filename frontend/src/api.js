const API_BASE = '/api';

export const api = {
  // Ingestion
  async getDocuments(status = '') {
    const url = status ? `${API_BASE}/ingestion/documents/?status=${encodeURIComponent(status)}` : `${API_BASE}/ingestion/documents/`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async getDocument(id) {
    const res = await fetch(`${API_BASE}/ingestion/documents/${id}/`);
    if (!res.ok) throw new Error('Failed to fetch document');
    return res.json();
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/ingestion/upload/`, {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to upload document');
    return data;
  },

  async deleteDocument(id) {
    const res = await fetch(`${API_BASE}/ingestion/documents/${id}/`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  },

  async reprocessDocument(id) {
    const res = await fetch(`${API_BASE}/ingestion/documents/${id}/reprocess/`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to reprocess document');
    return res.json();
  },

  // Retrieval
  async search({ query, top_k = 6, method = 'hybrid', filters = {}, rerank = false, min_score = 0.1 }) {
    const res = await fetch(`${API_BASE}/retrieval/search/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k, method, filters, rerank, min_score }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Search failed');
    return data;
  },

  async validateCitations({ text, retrieved_chunks }) {
    const res = await fetch(`${API_BASE}/retrieval/validate-citations/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, retrieved_chunks }),
    });
    if (!res.ok) throw new Error('Citation validation failed');
    return res.json();
  },

  // Claims
  async getClaims(filters = {}) {
    const params = new URLSearchParams();
    if (filters.document_id) params.append('document_id', filters.document_id);
    if (filters.review_status) params.append('review_status', filters.review_status);
    if (filters.entity) params.append('entity', filters.entity);
    if (filters.min_confidence) params.append('min_confidence', filters.min_confidence);

    const res = await fetch(`${API_BASE}/claims/?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch claims');
    return res.json();
  },

  async reviewClaim(claimId, decision, notes = '') {
    const res = await fetch(`${API_BASE}/claims/${claimId}/review/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes }),
    });
    if (!res.ok) throw new Error('Failed to submit claim review');
    return res.json();
  },

  async getRelationships(filters = {}) {
    const params = new URLSearchParams();
    if (filters.type) params.append('type', filters.type);
    if (filters.status) params.append('status', filters.status);

    const res = await fetch(`${API_BASE}/claims/relationships/list/?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch relationships');
    return res.json();
  },

  async reviewRelationship(relId, decision, notes = '', corrected_type = null) {
    const res = await fetch(`${API_BASE}/claims/relationships/${relId}/review/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes, corrected_type }),
    });
    if (!res.ok) throw new Error('Failed to submit relationship review');
    return res.json();
  },

  async getContradictions(status = '') {
    const url = status ? `${API_BASE}/claims/contradictions/queue/?status=${encodeURIComponent(status)}` : `${API_BASE}/claims/contradictions/queue/`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch contradiction queue');
    return res.json();
  },

  async getComparisonMatrix(document_ids = [], topic = '') {
    const res = await fetch(`${API_BASE}/claims/matrix/compare/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_ids, topic }),
    });
    if (!res.ok) throw new Error('Failed to fetch comparison matrix');
    return res.json();
  },

  // Knowledge Graph
  async getKnowledgeGraph(document_id = '', topic = '', include_evidence = true) {
    const params = new URLSearchParams();
    if (document_id) params.append('document_id', document_id);
    if (topic) params.append('topic', topic);
    params.append('include_evidence', include_evidence ? 'true' : 'false');

    const res = await fetch(`${API_BASE}/graph/data/?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch knowledge graph');
    return res.json();
  },

  // Agents
  async runResearchWorkflow(query, mode = 'deep_research') {
    const res = await fetch(`${API_BASE}/agents/research/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, mode }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Agent workflow execution failed');
    return data;
  },

  async getResearchHistory() {
    const res = await fetch(`${API_BASE}/agents/history/`);
    if (!res.ok) throw new Error('Failed to fetch research history');
    return res.json();
  },

  // Evaluation
  async getEvaluationRuns() {
    const res = await fetch(`${API_BASE}/evaluation/runs/`);
    if (!res.ok) throw new Error('Failed to fetch evaluation runs');
    return res.json();
  },

  async runBenchmark(run_name = '') {
    const res = await fetch(`${API_BASE}/evaluation/runs/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_name }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Benchmark run failed');
    return data;
  },
};
