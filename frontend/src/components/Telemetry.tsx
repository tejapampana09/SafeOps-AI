import React from 'react';
import { SensorData } from '../hooks/useWebSocket';

interface TelemetryProps {
  sensors: SensorData[];
}

export const Telemetry: React.FC<TelemetryProps> = ({ sensors }) => {
  return (
    <div className="card telemetry-container">
      <div className="card-header">
        <h3>📊 Real-Time SCADA Telemetry</h3>
        <span className="badge badge-success">Live Stream</span>
      </div>
      <div className="table-responsive">
        <table className="telemetry-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Sensor Name</th>
              <th>Location</th>
              <th className="text-right">Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {sensors.map((sensor) => {
              let statusClass = 'indicator-safe';
              if (sensor.status === 'CRITICAL') {
                statusClass = 'indicator-critical';
              } else if (sensor.status === 'WARNING') {
                statusClass = 'indicator-warning';
              }

              return (
                <tr key={sensor.id}>
                  <td className="monospace bold">{sensor.id}</td>
                  <td>{sensor.name}</td>
                  <td className="text-muted text-small">{sensor.location.split(' - ')[0]}</td>
                  <td className="text-right bold monospace">
                    {sensor.current_value.toFixed(1)} <span className="unit-label">{sensor.unit}</span>
                  </td>
                  <td>
                    <div className="status-cell">
                      <span className={`status-indicator ${statusClass}`}></span>
                      <span className={`status-text-label ${sensor.status.toLowerCase()}`}>{sensor.status}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
