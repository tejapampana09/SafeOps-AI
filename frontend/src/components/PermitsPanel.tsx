import React from 'react';
import { PermitData, WorkerData } from '../hooks/useWebSocket';

interface PermitsPanelProps {
  permits: PermitData[];
  workers: WorkerData[];
}

export const PermitsPanel: React.FC<PermitsPanelProps> = ({ permits, workers }) => {
  return (
    <div className="card permits-container">
      <div className="card-header">
        <h3>🔑 Active Permits-to-Work (PTW)</h3>
        <span className="badge badge-brand">e-PTW Registry</span>
      </div>
      <div className="permits-list">
        {permits.map((permit) => {
          const activeWorkers = workers.filter(w => w.active_permit_id === permit.id);
          
          let permitStatusClass = 'permit-approved';
          if (permit.status === 'REVOKED') {
            permitStatusClass = 'permit-revoked';
          } else if (permit.status === 'EXPIRED') {
            permitStatusClass = 'permit-expired';
          }

          const hazards = JSON.parse(permit.hazards_declared) as string[];
          const precautions = JSON.parse(permit.precautions_taken) as string[];

          return (
            <div key={permit.id} className={`permit-card ${permitStatusClass}`}>
              <div className="permit-header">
                <div>
                  <span className="monospace bold permit-id">{permit.id}</span>
                  <span className="permit-type-tag">{permit.type.replace('_', ' ')}</span>
                </div>
                <span className={`status-badge ${permitStatusClass}`}>{permit.status}</span>
              </div>
              
              <div className="permit-details">
                <div className="detail-item">
                  <strong>Location:</strong> {permit.location}
                </div>
                <div className="detail-item">
                  <strong>Issued To:</strong> {permit.issued_to}
                </div>
              </div>

              <div className="permit-lists-grid">
                <div>
                  <div className="list-title">⚠️ Declared Hazards</div>
                  <ul className="bullet-list">
                    {hazards.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="list-title">🛡️ Safety Precautions</div>
                  <ul className="bullet-list">
                    {precautions.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {activeWorkers.length > 0 && (
                <div className="permit-workers-assigned">
                  <div className="list-title">👥 Assigned Personnel ({activeWorkers.length})</div>
                  <div className="workers-row">
                    {activeWorkers.map((w) => (
                      <div key={w.id} className="worker-detail-tag">
                        <span>{w.name} ({w.role})</span>
                        <span className={`ppe-indicator ${w.ppe_status.toLowerCase()}`}>
                          PPE: {w.ppe_status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
