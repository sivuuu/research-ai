import React, { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import EvidenceDrawer from '../components/EvidenceDrawer';

export default function KnowledgeGraphPage() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], stats: {} });
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState('');
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const canvasRef = useRef(null);

  // Graph physics state
  const nodesRef = useRef([]);
  const edgesRef = useRef([]);
  const animFrameRef = useRef(null);
  const transformRef = useRef({ x: 0, y: 0, scale: 1 });
  const draggingNodeRef = useRef(null);
  const panningRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });

  const loadGraph = async () => {
    setIsLoading(true);
    try {
      const [gData, docsData] = await Promise.all([
        api.getKnowledgeGraph(selectedDocId, '', includeEvidence),
        api.getDocuments()
      ]);
      setGraphData(gData);
      setDocuments(docsData.documents || []);

      // Initialize node positions
      const width = canvasRef.current ? canvasRef.current.width : 900;
      const height = canvasRef.current ? canvasRef.current.height : 600;

      const initializedNodes = (gData.nodes || []).map((node, i) => {
        const angle = (i / Math.max(1, gData.nodes.length)) * 2 * Math.PI;
        const radius = 180 + Math.random() * 120;
        return {
          ...node,
          x: width / 2 + Math.cos(angle) * radius,
          y: height / 2 + Math.sin(angle) * radius,
          vx: 0,
          vy: 0,
          radius: getNodeRadius(node.type),
          color: getNodeColor(node.type, node.metadata?.review_status)
        };
      });

      nodesRef.current = initializedNodes;
      edgesRef.current = gData.edges || [];
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [selectedDocId, includeEvidence]);

  const getNodeRadius = (type) => {
    switch (type) {
      case 'document': return 22;
      case 'author': return 16;
      case 'topic': return 18;
      case 'claim': return 15;
      case 'entity': return 12;
      case 'evidence_passage': return 10;
      default: return 14;
    }
  };

  const getNodeColor = (type, status) => {
    switch (type) {
      case 'document': return '#38bdf8'; // Cyan
      case 'author': return '#10b981';   // Emerald
      case 'topic': return '#6366f1';    // Indigo
      case 'claim': return status === 'REJECTED' ? '#f43f5e' : '#f59e0b'; // Amber / Rose
      case 'entity': return '#a855f7';   // Violet
      case 'evidence_passage': return '#94a3b8'; // Slate
      default: return '#cbd5e1';
    }
  };

  // Canvas render & force loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const updateSimulation = () => {
      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const nodeMap = new Map(nodes.map(n => [n.id, n]));

      // 1. Repulsion between nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const na = nodes[i];
          const nb = nodes[j];
          const dx = nb.x - na.x;
          const dy = nb.y - na.y;
          const distSq = dx * dx + dy * dy || 1;
          const dist = Math.sqrt(distSq);

          if (dist < 260) {
            const force = (260 - dist) / dist * 0.08;
            na.vx -= dx * force;
            na.vy -= dy * force;
            nb.vx += dx * force;
            nb.vy += dy * force;
          }
        }
      }

      // 2. Attraction along edges
      for (const e of edges) {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (src && tgt) {
          const dx = tgt.x - src.x;
          const dy = tgt.y - src.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const desired = e.type === 'GROUNDED_IN' ? 80 : 140;
          const force = (dist - desired) * 0.005;
          src.vx += (dx / dist) * force;
          src.vy += (dy / dist) * force;
          tgt.vx -= (dx / dist) * force;
          tgt.vy -= (dy / dist) * force;
        }
      }

      // 3. Center gravity and damping
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      for (const n of nodes) {
        if (n !== draggingNodeRef.current) {
          n.vx += (cx - n.x) * 0.0005;
          n.vy += (cy - n.y) * 0.0005;
          n.vx *= 0.88;
          n.vy *= 0.88;
          n.x += n.vx;
          n.y += n.vy;
        }
      }

      // Draw frame
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      ctx.translate(transformRef.current.x, transformRef.current.y);
      ctx.scale(transformRef.current.scale, transformRef.current.scale);

      // Draw edges
      for (const e of edges) {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (src && tgt) {
          ctx.beginPath();
          ctx.moveTo(src.x, src.y);
          ctx.lineTo(tgt.x, tgt.y);

          if (e.type === 'CONTRADICTS') {
            ctx.strokeStyle = 'rgba(244, 63, 94, 0.7)';
            ctx.lineWidth = 2;
          } else if (e.type === 'SUPPORTS') {
            ctx.strokeStyle = 'rgba(16, 185, 129, 0.5)';
            ctx.lineWidth = 1.5;
          } else {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
            ctx.lineWidth = 1;
          }
          ctx.stroke();

          // Edge type label
          if (transformRef.current.scale > 0.8) {
            const midX = (src.x + tgt.x) / 2;
            const midY = (src.y + tgt.y) / 2;
            ctx.font = '9px var(--font-mono, monospace)';
            ctx.fillStyle = e.type === 'CONTRADICTS' ? '#fda4af' : '#94a3b8';
            ctx.fillText(e.type, midX, midY);
          }
        }
      }

      // Draw nodes
      for (const n of nodes) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = n === selectedNode ? 16 : 4;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.strokeStyle = n === selectedNode ? '#ffffff' : 'rgba(255, 255, 255, 0.2)';
        ctx.lineWidth = n === selectedNode ? 2.5 : 1;
        ctx.stroke();

        // Node label
        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.fillText(n.label.substring(0, 18), n.x, n.y + n.radius + 12);
      }

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(updateSimulation);
    };

    animFrameRef.current = requestAnimationFrame(updateSimulation);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [selectedNode]);

  // Mouse interaction handlers
  const handleMouseDown = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - transformRef.current.x) / transformRef.current.scale;
    const mouseY = (e.clientY - rect.top - transformRef.current.y) / transformRef.current.scale;

    // Check hit node
    const hitNode = nodesRef.current.find(n => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 4;
    });

    if (hitNode) {
      draggingNodeRef.current = hitNode;
      setSelectedNode(hitNode);
      if (hitNode.type === 'claim' || hitNode.type === 'evidence_passage') {
        setSelectedEvidence({
          document_title: hitNode.metadata?.document_title,
          page_number: hitNode.metadata?.page_number,
          section_title: hitNode.metadata?.section,
          text: hitNode.metadata?.supporting_passage || hitNode.metadata?.text,
          score: hitNode.metadata?.confidence
        });
      }
    } else {
      panningRef.current = true;
      lastMousePosRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseMove = (e) => {
    if (draggingNodeRef.current) {
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      draggingNodeRef.current.x = (e.clientX - rect.left - transformRef.current.x) / transformRef.current.scale;
      draggingNodeRef.current.y = (e.clientY - rect.top - transformRef.current.y) / transformRef.current.scale;
    } else if (panningRef.current) {
      const dx = e.clientX - lastMousePosRef.current.x;
      const dy = e.clientY - lastMousePosRef.current.y;
      transformRef.current.x += dx;
      transformRef.current.y += dy;
      lastMousePosRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseUp = () => {
    draggingNodeRef.current = null;
    panningRef.current = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const newScale = Math.min(2.5, Math.max(0.4, transformRef.current.scale * zoomFactor));
    transformRef.current.scale = newScale;
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Interactive Knowledge Graph</h1>
          <p className="page-subtitle">
            Visual property graph connecting Documents, Authors, Topics, Entities, Claims, and Evidence Passages with edge provenance.
          </p>
        </div>
      </div>

      {/* Graph Controls Bar */}
      <div className="card" style={{ padding: '14px 20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Focus Document:</span>
            <select
              className="select"
              style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              id="graph-doc-select"
            >
              <option value="">All Documents</option>
              {documents.map(d => (
                <option key={d.id} value={d.id}>{d.title.substring(0, 32)}...</option>
              ))}
            </select>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={includeEvidence}
              onChange={(e) => setIncludeEvidence(e.target.checked)}
              id="graph-evidence-toggle"
            />
            <span>Show Evidence Passage Nodes</span>
          </label>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', fontSize: '0.78rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#38bdf8' }}></span> Document
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }}></span> Author
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#a855f7' }}></span> Entity
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }}></span> Claim
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f43f5e' }}></span> Contradiction Edge
          </span>
        </div>
      </div>

      {/* Canvas Viewport */}
      <div className="card" style={{ padding: '0', overflow: 'hidden', position: 'relative', height: '620px' }}>
        {isLoading && (
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(7,9,14,0.7)', zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="spinner"></div>
          </div>
        )}

        <canvas
          ref={canvasRef}
          width={1120}
          height={620}
          style={{ width: '100%', height: '100%', cursor: 'grab', display: 'block' }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          id="knowledge-graph-canvas"
        />

        {/* Node Inspector Floating Badge */}
        {selectedNode && (
          <div style={{
            position: 'absolute',
            bottom: '20px',
            left: '20px',
            background: 'var(--bg-glass)',
            backdropFilter: 'blur(16px)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px 18px',
            maxWidth: '380px',
            zIndex: 5
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span className="badge badge-cyan">{selectedNode.type.toUpperCase()}</span>
              <button
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem' }}
                onClick={() => setSelectedNode(null)}
              >
                ✕
              </button>
            </div>
            <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.9rem', marginBottom: '4px' }}>
              {selectedNode.metadata?.full_title || selectedNode.metadata?.full_text || selectedNode.label}
            </div>
            {selectedNode.metadata?.page_number && (
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
                Page {selectedNode.metadata.page_number} § {selectedNode.metadata.section || 'General'}
              </div>
            )}
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
