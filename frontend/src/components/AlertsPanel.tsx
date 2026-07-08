import React from 'react';
import { AlertResponse } from '../hooks/useWebSocket';

interface AlertsPanelProps {
  alerts: AlertResponse[];
  onAcknowledge: (alertId: string) => void;
  onViewReport: (alertId: string) => void;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({ alerts, onAcknowledge, onViewReport }) => {
  const activeAlerts = alerts.filter(a => a.status === 'ACTIVE');
  const acknowledgedAlerts = alerts.filter(a => a.status === 'ACKNOWLEDGED').slice(0, 5); // show last 5

  return (
    <div className="card alerts-container">
      <div className="card-header">
        <h3>🚨 Emergency Safety Alarms</h3>
        <span className="badge badge-danger">{activeAlerts.length} Active</span>
      </div>
      
      {activeAlerts.length === 0 && (
        <div className="alerts-empty">
          <div className="shield-icon">🛡️</div>
          <p>No active safety alarms. All parameters normal.</p>
        </div>
      )}

      <div className="alerts-list">
        {activeAlerts.map((alert) => (
          <div key={alert.id} className={`alert-item-card severity-${alert.severity.toLowerCase()}`}>
            <div className="alert-item-header">
              <span className="alert-badge">{alert.severity}</span>
              <span className="monospace alert-id-text">{alert.id}</span>
            </div>
            
            <div className="alert-message">{alert.description}</div>
            
            <div className="alert-meta">
              <span>📍 {alert.location}</span>
              <span>🕒 {new Date(alert.timestamp).toLocaleTimeString()}</span>
            </div>

            <div className="alert-actions">
              <button 
                className="btn btn-warning btn-sm"
                onClick={() => onAcknowledge(alert.id)}
              >
                Acknowledge Alarm
              </button>
              {alert.severity === 'CRITICAL' && (
                <button 
                  className="btn btn-secondary btn-sm"
                  onClick={() => onViewReport(alert.id)}
                >
                  📄 View Incident Report
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {acknowledgedAlerts.length > 0 && (
        <div className="acknowledged-section">
          <h4>Acknowledged Alarms (History)</h4>
          <div className="acknowledged-list">
            {acknowledgedAlerts.map((alert) => (
              <div key={alert.id} className="acknowledged-item">
                <span className="monospace text-small">{alert.id}</span>
                <span className="text-small">{alert.location.split(' - ')[0]}</span>
                <span className="badge badge-secondary text-small">ACKNOWLEDGED</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
