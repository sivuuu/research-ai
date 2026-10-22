import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Bar, Radar } from 'react-chartjs-2';
import { api } from '../api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function EvaluationDashboardPage() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const loadRuns = async () => {
    try {
      const data = await api.getEvaluationRuns();
      const runList = data.runs || [];
      setRuns(runList);
      if (runList.length > 0 && !selectedRun) {
        setSelectedRun(runList[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  const handleRunBenchmark = async () => {
    setIsRunning(true);
    setError('');
    setSuccessMsg('');
    try {
      const result = await api.runBenchmark();
      setSuccessMsg(`Benchmark run '${result.run_name}' completed successfully!`);
      await loadRuns();
      // Select the new run
      const updated = await api.getEvaluationRuns();
      if (updated.runs?.length > 0) {
        setSelectedRun(updated.runs[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  // Chart data setup
  const barChartData = selectedRun ? {
    labels: [
      'Recall@1',
      'Recall@3',
      'Recall@5',
      'MRR',
      'Citation Prec',
      'Citation Cov',
      'Claim Prec',
      'Claim Rec',
      'Contradiction Prec',
      'Faithfulness'
    ],
    datasets: [
      {
        label: `${selectedRun.run_name} Score`,
        data: [
          selectedRun.recall_at_1,
          selectedRun.recall_at_3,
          selectedRun.recall_at_5,
          selectedRun.mrr,
          selectedRun.citation_precision,
          selectedRun.citation_coverage,
          selectedRun.claim_extraction_precision,
          selectedRun.claim_extraction_recall,
          selectedRun.contradiction_precision,
          selectedRun.answer_faithfulness
        ],
        backgroundColor: [
          'rgba(56, 189, 248, 0.7)',
          'rgba(56, 189, 248, 0.85)',
          'rgba(56, 189, 248, 1)',
          'rgba(99, 102, 241, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(16, 185, 129, 0.6)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(168, 85, 247, 0.6)',
          'rgba(244, 63, 94, 0.8)',
          'rgba(245, 158, 11, 0.8)'
        ],
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  } : null;

  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        min: 0,
        max: 1.0,
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8' }
      },
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 11 } }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => `Score: ${(ctx.raw * 100).toFixed(1)}%`
        }
      }
    }
  };

  const radarChartData = selectedRun ? {
    labels: [
      'Retrieval (R@5)',
      'Ranking (MRR)',
      'Citation Precision',
      'Citation Coverage',
      'Claim F1',
      'Contradiction F1',
      'Faithfulness'
    ],
    datasets: [
      {
        label: 'System Performance Radar',
        data: [
          selectedRun.recall_at_5,
          selectedRun.mrr,
          selectedRun.citation_precision,
          selectedRun.citation_coverage,
          selectedRun.claim_extraction_precision,
          selectedRun.contradiction_precision,
          selectedRun.answer_faithfulness
        ],
        backgroundColor: 'rgba(56, 189, 248, 0.2)',
        borderColor: '#38bdf8',
        borderWidth: 2,
        pointBackgroundColor: '#6366f1',
        pointBorderColor: '#ffffff'
      }
    ]
  } : null;

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 1.0,
        ticks: { display: false },
        grid: { color: 'rgba(255, 255, 255, 0.08)' },
        angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
        pointLabels: { color: '#e2e8f0', font: { size: 11 } }
      }
    },
    plugins: { legend: { display: false } }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Evaluation & Benchmark Framework</h1>
          <p className="page-subtitle">
            Scientific measurement across Recall@K, MRR ranking, citation coverage, claim extraction F1, contradiction precision, and end-to-end latency.
          </p>
        </div>
        <div>
          <button
            className="btn btn-primary"
            onClick={handleRunBenchmark}
            disabled={isRunning}
            id="run-benchmark-btn"
          >
            {isRunning ? (
              <>
                <span className="spinner" style={{ width: 14, height: 14 }}></span> Running Benchmark Suite...
              </>
            ) : (
              <>▶ Execute Benchmark Suite</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(244, 63, 94, 0.15)', color: '#fda4af', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {successMsg && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#6ee7b7', padding: '12px 16px', borderRadius: '8px', marginBottom: '20px' }}>
          ✓ {successMsg}
        </div>
      )}

      {/* Selected Run Metrics Summary Cards */}
      {selectedRun && (
        <div className="grid-4" style={{ marginBottom: '24px' }}>
          <div className="card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Retrieval Recall@5</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
              {(selectedRun.recall_at_5 * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              MRR: {selectedRun.mrr.toFixed(3)}
            </div>
          </div>

          <div className="card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Citation Precision</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
              {(selectedRun.citation_precision * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Coverage: {(selectedRun.citation_coverage * 100).toFixed(1)}%
            </div>
          </div>

          <div className="card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Contradiction Precision</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-rose)' }}>
              {(selectedRun.contradiction_precision * 100).toFixed(1)}%
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Recall: {(selectedRun.contradiction_recall * 100).toFixed(1)}%
            </div>
          </div>

          <div className="card" style={{ padding: '18px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Average Latency</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
              {selectedRun.average_latency_ms.toFixed(0)} ms
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Faithfulness: {(selectedRun.answer_faithfulness * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      {selectedRun && (
        <div className="grid-2" style={{ marginBottom: '28px' }}>
          <div className="card" style={{ height: '360px', padding: '20px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
              Core Metric Scores (0.0 to 1.0)
            </h3>
            <div style={{ height: '280px' }}>
              {barChartData && <Bar data={barChartData} options={barChartOptions} />}
            </div>
          </div>

          <div className="card" style={{ height: '360px', padding: '20px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
              Multi-Dimensional Grounding Radar
            </h3>
            <div style={{ height: '280px' }}>
              {radarChartData && <Radar data={radarChartData} options={radarOptions} />}
            </div>
          </div>
        </div>
      )}

      {/* Per-Query Diagnostic Table */}
      {selectedRun && selectedRun.metrics_details?.diagnostics && (
        <div className="card" style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
            Per-Query Diagnostic Trace ({selectedRun.metrics_details.diagnostics.length} Test Cases)
          </h3>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Test Query ID</th>
                  <th>Question</th>
                  <th>Recall@3</th>
                  <th>MRR</th>
                  <th>Citation Prec</th>
                  <th>Faithfulness</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {selectedRun.metrics_details.diagnostics.map((d, i) => (
                  <tr key={i}>
                    <td><span className="badge badge-violet">{d.id}</span></td>
                    <td style={{ color: '#ffffff', fontWeight: 500, maxWidth: '340px' }}>{d.question}</td>
                    <td><span className="badge badge-cyan">{(d.recall_at_3 * 100).toFixed(0)}%</span></td>
                    <td>{d.mrr.toFixed(2)}</td>
                    <td><span className="badge badge-emerald">{(d.citation_precision * 100).toFixed(0)}%</span></td>
                    <td><span className="badge badge-amber">{(d.faithfulness * 100).toFixed(0)}%</span></td>
                    <td style={{ color: 'var(--text-muted)' }}>{d.latency_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Run History List */}
      <div className="card">
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginBottom: '14px' }}>
          Evaluation Run History ({runs.length})
        </h3>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Run Name</th>
                <th>Dataset</th>
                <th>Recall@5</th>
                <th>Citation Prec</th>
                <th>Claim F1</th>
                <th>Contradiction Prec</th>
                <th>Avg Latency</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} style={{ background: selectedRun?.id === r.id ? 'rgba(56, 189, 248, 0.08)' : 'transparent' }}>
                  <td style={{ fontWeight: 600, color: '#ffffff' }}>{r.run_name}</td>
                  <td><span className="badge badge-gray">{r.dataset_name}</span></td>
                  <td>{(r.recall_at_5 * 100).toFixed(1)}%</td>
                  <td>{(r.citation_precision * 100).toFixed(1)}%</td>
                  <td>{(r.claim_extraction_precision * 100).toFixed(1)}%</td>
                  <td>{(r.contradiction_precision * 100).toFixed(1)}%</td>
                  <td>{r.average_latency_ms.toFixed(0)} ms</td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setSelectedRun(r)}
                    >
                      {selectedRun?.id === r.id ? 'Viewing' : 'Inspect'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
