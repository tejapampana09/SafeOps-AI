import React from 'react';
import { SensorData, WorkerData } from '../hooks/useWebSocket';

interface HeatmapProps {
  sensors: SensorData[];
  workers: WorkerData[];
  compoundRiskScore: number;
}

export const Heatmap: React.FC<HeatmapProps> = ({ sensors, workers, compoundRiskScore }) => {
  // Define sectors and map their data
  const sectors = [
    {
      id: 'SEC1',
      name: 'Sector 1: Coke Oven Battery',
      shortName: 'Sector 1',
      description: 'High thermal and coal-gas processing zone.',
      sensorsFilter: (s: SensorData) => s.location.includes('Sector 1'),
      workersFilter: (w: WorkerData) => w.current_location.includes('Sector 1'),
      baseWeight: 0.3
    },
    {
      id: 'SEC2',
      name: 'Sector 2: Storage Tanks (Confined)',
      shortName: 'Sector 2',
      description: 'Volatile fuel tanks & confined entry hazard.',
      sensorsFilter: (s: SensorData) => s.location.includes('Sector 2'),
      workersFilter: (w: WorkerData) => w.current_location.includes('Sector 2'),
      baseWeight: 0.4
    },
    {
      id: 'SEC3',
      name: 'Sector 3: Utility Block (Boilers)',
      shortName: 'Sector 3',
      description: 'High-pressure steam boiler station.',
      sensorsFilter: (s: SensorData) => s.location.includes('Sector 3'),
      workersFilter: (w: WorkerData) => w.current_location.includes('Sector 3'),
      baseWeight: 0.2
    },
    {
      id: 'SEC4',
      name: 'Sector 4: Ammonia Loading Bay',
      shortName: 'Sector 4',
      description: 'Chemical transit & cargo handling.',
      sensorsFilter: (s: SensorData) => s.location.includes('Sector 4'),
      workersFilter: (w: WorkerData) => w.current_location.includes('Sector 4'),
      baseWeight: 0.1
    }
  ];

  return (
    <div className="card heatmap-container">
      <div className="card-header">
        <h3>📍 Geospatial Plant Safety Heatmap</h3>
        <span className="badge badge-info">2D Facility Layout</span>
      </div>
      <div className="heatmap-grid">
        {sectors.map((sector) => {
          const localSensors = sensors.filter(sector.sensorsFilter);
          const localWorkers = workers.filter(sector.workersFilter);
          
          // Calculate local sector risk score
          let localRisk = 5;
          const hasCriticalSensor = localSensors.some(s => s.status === 'CRITICAL');
          const hasWarningSensor = localSensors.some(s => s.status === 'WARNING');
          const hasPPEBreach = localWorkers.some(w => w.ppe_status !== 'FULL');

          if (hasCriticalSensor) {
            localRisk = 85;
          } else if (hasWarningSensor || hasPPEBreach) {
            localRisk = 55;
          } else if (localWorkers.length > 0) {
            localRisk = 20; // baseline operational risk when personnel is active
          }

          // Override for simulated scenarios
          if (sector.id === 'SEC1' && compoundRiskScore >= 75 && hasCriticalSensor) {
            localRisk = compoundRiskScore;
          }
          if (sector.id === 'SEC3' && compoundRiskScore >= 70 && hasCriticalSensor) {
            localRisk = compoundRiskScore;
          }
          if (sector.id === 'SEC2' && hasPPEBreach) {
            localRisk = Math.max(localRisk, compoundRiskScore);
          }

          // Determine status level
          let statusClass = 'status-safe';
          let statusLabel = 'NORMAL';
          if (localRisk >= 75) {
            statusClass = 'status-critical';
            statusLabel = 'CRITICAL';
          } else if (localRisk >= 40) {
            statusClass = 'status-warning';
            statusLabel = 'WARNING';
          }

          return (
            <div key={sector.id} className={`sector-card ${statusClass}`}>
              <div className="sector-header">
                <h4>{sector.shortName}</h4>
                <span className={`sector-badge ${statusClass}`}>{statusLabel}</span>
              </div>
              <div className="sector-title">{sector.name.split(': ')[1]}</div>
              
              <div className="sector-stats">
                <div className="stat-row">
                  <span>Sensors:</span>
                  <span className="stat-val">{localSensors.length} active</span>
                </div>
                <div className="stat-row">
                  <span>Personnel:</span>
                  <span className="stat-val">{localWorkers.length} present</span>
                </div>
                <div className="stat-row">
                  <span>Local Hazard index:</span>
                  <span className="stat-val bold">{localRisk}%</span>
                </div>
              </div>

              {localWorkers.length > 0 && (
                <div className="sector-workers">
                  {localWorkers.map(w => (
                    <div key={w.id} className="worker-tag">
                      👤 {w.name} {w.ppe_status !== 'FULL' && <span className="warning-dot" title="PPE violation!">⚠️</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
