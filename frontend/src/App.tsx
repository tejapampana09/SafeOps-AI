import { useState, useEffect } from 'react';
import { useWebSocket, AlertResponse } from './hooks/useWebSocket';
import { Heatmap } from './components/Heatmap';
import { Telemetry } from './components/Telemetry';
import { PermitsPanel } from './components/PermitsPanel';
import { AlertsPanel } from './components/AlertsPanel';
import { AgentReasoning } from './components/AgentReasoning';
import { CCTVLog } from './components/CCTVLog';

interface IncidentReportDetail {
  id: string;
  alert_id: string;
  timestamp: string;
  sector: string;
  summary: string;
  timeline: string; // JSON string
  regulatory_violations: string; // JSON string
  evacuation_status: string;
  authorities_notified: string; // JSON string
}

function App() {
  // Determine API URL (supports local and docker compose setups)
  const apiHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
  const wsUrl = `ws://${apiHost}:8000/ws/telemetry`;
  const restUrl = `http://${apiHost}:8000/api`;

  const { isConnected, telemetry, safetyEvaluation, cctvEvents, clearCctvEvents } = useWebSocket(wsUrl);
  
  const [activeScenario, setActiveScenario] = useState('NORMAL');
  const [allAlerts, setAllAlerts] = useState<AlertResponse[]>([]);
  const [selectedReport, setSelectedReport] = useState<IncidentReportDetail | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);

  // Fetch alerts history on mount & when safetyEvaluation updates
  const fetchAlertsHistory = async () => {
    try {
      const res = await fetch(`${restUrl}/alerts/history`);
      if (res.ok) {
        const data = await res.json();
        setAllAlerts(data);
      }
    } catch (err) {
      console.error('Failed to fetch alerts history:', err);
    }
  };

  useEffect(() => {
    fetchAlertsHistory();
  }, [safetyEvaluation]);

  // Handle Scenario trigger API
  const handleScenarioChange = async (scenarioId: string) => {
    try {
      const res = await fetch(`${restUrl}/simulator/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId })
      });
      if (res.ok) {
        setActiveScenario(scenarioId);
      }
    } catch (err) {
      console.error('Failed to trigger scenario:', err);
    }
  };

  // Handle Acknowledge Alert API
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const res = await fetch(`${restUrl}/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });
      if (res.ok) {
        fetchAlertsHistory();
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  // Handle View Incident Report API
  const handleViewIncidentReport = async (alertId: string) => {
    try {
      const res = await fetch(`${restUrl}/alerts/${alertId}/report`);
      if (res.ok) {
        const report = await res.json();
        setSelectedReport(report);
        setShowReportModal(true);
      } else {
        alert('No formal incident report generated yet. Ensure risk is in CRITICAL state.');
      }
    } catch (err) {
      console.error('Failed to fetch incident report:', err);
    }
  };

  // Determine global status
  const currentRiskScore = safetyEvaluation ? safetyEvaluation.compound_risk_score : 5;
  let statusBadgeClass = 'badge-success';
  let systemStatusText = 'SYSTEM SECURE';

  if (currentRiskScore >= 75) {
    statusBadgeClass = 'badge-danger pulse-siren';
    systemStatusText = 'HAZARD THREAT TRIGGERED';
  } else if (currentRiskScore >= 40) {
    statusBadgeClass = 'badge-warning';
    systemStatusText = 'WARNING DRIFT DETECTED';
  }

  return (
    <div className="cockpit-app">
      {/* Top Banner Header */}
      <header className="cockpit-header">
        <div className="header-brand">
          <span className="logo-icon">🛡️</span>
          <div>
            <h1>SafeOps AI</h1>
            <p className="subtitle monospace">Zero-Harm Industrial Safety Command Panel</p>
          </div>
        </div>
        
        {/* Scenario Controls Panel */}
        <div className="scenario-controls">
          <span className="control-label text-small">SIMULATOR SANDBOX:</span>
          <div className="btn-group">
            <button 
              className={`btn btn-sm ${activeScenario === 'NORMAL' ? 'btn-brand' : 'btn-secondary'}`}
              onClick={() => handleScenarioChange('NORMAL')}
            >
              Normal Ops
            </button>
            <button 
              className={`btn btn-sm ${activeScenario === 'GAS_LEAK' ? 'btn-warning-glow' : 'btn-secondary'}`}
              onClick={() => handleScenarioChange('GAS_LEAK')}
            >
              Gas Leak
            </button>
            <button 
              className={`btn btn-sm ${activeScenario === 'HOT_WORK_CONFLICT' ? 'btn-warning-glow' : 'btn-secondary'}`}
              onClick={() => handleScenarioChange('HOT_WORK_CONFLICT')}
            >
              Hot Work Conflict
            </button>
            <button 
              className={`btn btn-sm ${activeScenario === 'UNAUTHORIZED_WORKER' ? 'btn-warning-glow' : 'btn-secondary'}`}
              onClick={() => handleScenarioChange('UNAUTHORIZED_WORKER')}
            >
              Unauthorized Worker
            </button>
            <button 
              className={`btn btn-sm ${activeScenario === 'COMBINED_COMPOUND_RISK' ? 'btn-danger-glow' : 'btn-secondary'}`}
              onClick={() => handleScenarioChange('COMBINED_COMPOUND_RISK')}
            >
              Compound Risk (Critical)
            </button>
          </div>
        </div>

        <div className="header-status">
          <div className={`status-pill badge ${statusBadgeClass}`}>
            <span className="dot"></span> {systemStatusText} (Risk: {currentRiskScore}%)
          </div>
          <div className="connection-pill monospace text-small">
            <span className={`connection-dot ${isConnected ? 'online' : 'offline'}`}></span>
            {isConnected ? 'WS ONLINE' : 'WS CONNECTING...'}
          </div>
        </div>
      </header>

      {/* Main Grid Body */}
      {telemetry ? (
        <main className="cockpit-grid">
          {/* Column 1: Heatmap and Alarms list */}
          <div className="grid-column flex-column">
            <Heatmap 
              sensors={telemetry.sensors} 
              workers={telemetry.workers} 
              compoundRiskScore={currentRiskScore} 
            />
            <AlertsPanel 
              alerts={allAlerts} 
              onAcknowledge={handleAcknowledgeAlert} 
              onViewReport={handleViewIncidentReport} 
            />
          </div>

          {/* Column 2: Telemetry and Permits registry */}
          <div className="grid-column flex-column">
            <Telemetry sensors={telemetry.sensors} />
            <PermitsPanel permits={telemetry.permits} workers={telemetry.workers} />
          </div>

          {/* Column 3: Safety Council Reasoning and CCTV */}
          <div className="grid-column flex-column">
            <AgentReasoning evaluation={safetyEvaluation} />
            <CCTVLog events={cctvEvents} onClear={clearCctvEvents} />
          </div>
        </main>
      ) : (
        <div className="cockpit-loading">
          <div className="loading-spinner"></div>
          <p>Connecting to plant telemetry telemetry feeds...</p>
        </div>
      )}

      {/* Incident Report Modal */}
      {showReportModal && selectedReport && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h2>📄 Statutory Preliminary Incident Report</h2>
              <button className="btn-close" onClick={() => setShowReportModal(false)}>×</button>
            </div>
            <div className="modal-body monospace">
              <div className="report-doc">
                <div className="doc-section text-center">
                  <h3>PRELIMINARY ACCIDENT REPORT (REGULATORY FORM-22)</h3>
                  <p>In accordance with Factories Act 1948 Section 88 & OISD Guidelines</p>
                </div>
                <hr />
                <div className="doc-meta-grid">
                  <div><strong>Report ID:</strong> {selectedReport.id}</div>
                  <div><strong>Alert Ref:</strong> {selectedReport.alert_id}</div>
                  <div><strong>Timestamp:</strong> {new Date(selectedReport.timestamp).toLocaleString()}</div>
                  <div><strong>Sector Area:</strong> {selectedReport.sector}</div>
                </div>
                <hr />
                <div className="doc-field">
                  <strong>INCIDENT SUMMARY SUMMARY:</strong>
                  <p>{selectedReport.summary}</p>
                </div>
                <div className="doc-field">
                  <strong>EVACUATION LOG STATUS:</strong>
                  <span className="status-evac-tag">{selectedReport.evacuation_status}</span>
                </div>
                <hr />
                <div className="doc-field">
                  <strong>STATUTORY RULES BREACHED:</strong>
                  <ul>
                    {(JSON.parse(selectedReport.regulatory_violations) as string[]).map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>
                <hr />
                <div className="doc-field">
                  <strong>CHRONOLOGICAL TIMELINE CHRONOLOGY:</strong>
                  <div className="timeline-view">
                    {(JSON.parse(selectedReport.timeline) as { time: string; event: string }[]).map((t, i) => (
                      <div key={i} className="timeline-step">
                        <span className="time">{new Date(t.time).toLocaleTimeString()}</span> - <span className="event">{t.event}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <hr />
                <div className="doc-field">
                  <strong>REGULATORY NOTIFICATIONS DISPATCHED:</strong>
                  <div className="notified-row">
                    {(JSON.parse(selectedReport.authorities_notified) as string[]).map((a, i) => (
                      <span key={i} className="notified-badge">🚨 {a}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => window.print()}>🖨️ Export PDF / Print</button>
              <button className="btn btn-brand" onClick={() => setShowReportModal(false)}>Close Report</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
