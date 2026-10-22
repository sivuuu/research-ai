import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ResearchWorkspacePage from './pages/ResearchWorkspacePage';
import DocumentLibraryPage from './pages/DocumentLibraryPage';
import SearchResultsPage from './pages/SearchResultsPage';
import ClaimExplorerPage from './pages/ClaimExplorerPage';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage';
import ComparisonMatrixPage from './pages/ComparisonMatrixPage';
import ContradictionQueuePage from './pages/ContradictionQueuePage';
import ResearchReportPage from './pages/ResearchReportPage';
import EvaluationDashboardPage from './pages/EvaluationDashboardPage';

export default function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ResearchWorkspacePage />} />
            <Route path="/documents" element={<DocumentLibraryPage />} />
            <Route path="/search" element={<SearchResultsPage />} />
            <Route path="/claims" element={<ClaimExplorerPage />} />
            <Route path="/graph" element={<KnowledgeGraphPage />} />
            <Route path="/matrix" element={<ComparisonMatrixPage />} />
            <Route path="/contradictions" element={<ContradictionQueuePage />} />
            <Route path="/reports" element={<ResearchReportPage />} />
            <Route path="/reports/:id" element={<ResearchReportPage />} />
            <Route path="/evaluation" element={<EvaluationDashboardPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
