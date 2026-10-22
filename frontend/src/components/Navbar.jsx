import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="brand-container">
          <div className="brand-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="18" cy="5" r="3"></circle>
              <circle cx="6" cy="12" r="3"></circle>
              <circle cx="18" cy="19" r="3"></circle>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
              <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
            </svg>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="brand-title">ResearchGraph AI</span>
              <span className="brand-badge">Evidence System</span>
            </div>
          </div>
        </NavLink>

        <nav className="nav-links">
          <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-workspace">
            Workspace
          </NavLink>
          <NavLink to="/documents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-documents">
            Documents
          </NavLink>
          <NavLink to="/search" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-search">
            Search
          </NavLink>
          <NavLink to="/claims" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-claims">
            Claims
          </NavLink>
          <NavLink to="/graph" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-graph">
            Graph
          </NavLink>
          <NavLink to="/matrix" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-matrix">
            Matrix
          </NavLink>
          <NavLink to="/contradictions" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-contradictions">
            Contradictions
          </NavLink>
          <NavLink to="/evaluation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="nav-evaluation">
            Evaluation
          </NavLink>
        </nav>

        <div className="status-indicator">
          <span className="pulse-dot"></span>
          <span>Engine Online</span>
        </div>
      </div>
    </header>
  );
}
