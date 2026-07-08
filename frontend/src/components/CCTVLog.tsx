import React from 'react';
import { CCTVEvent } from '../hooks/useWebSocket';

interface CCTVLogProps {
  events: CCTVEvent[];
  onClear: () => void;
}

export const CCTVLog: React.FC<CCTVLogProps> = ({ events, onClear }) => {
  return (
    <div className="card cctv-container">
      <div className="card-header flex-header">
        <h3>📹 Live CCTV Event Analytics</h3>
        <div>
          <button className="btn btn-secondary btn-sm" onClick={onClear}>Clear Logs</button>
        </div>
      </div>
      <div className="cctv-log-console">
        {events.length === 0 ? (
          <div className="console-empty">Scanning live feeds... No events detected.</div>
        ) : (
          events.map((event, index) => {
            const timeStr = new Date(event.timestamp).toLocaleTimeString();
            let logClass = 'log-info';
            if (event.type === 'PPE_VIOLATION') {
              logClass = 'log-warning';
            } else if (event.type === 'UNAUTHORIZED_ENTRY') {
              logClass = 'log-danger';
            }

            return (
              <div key={index} className={`console-line ${logClass}`}>
                <span className="console-time">[{timeStr}]</span>
                <span className="console-type">[{event.type}]</span>
                <span className="console-message">{event.message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
