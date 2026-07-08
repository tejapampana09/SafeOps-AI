import React from 'react';
import { SafetyEvaluation } from '../hooks/useWebSocket';

interface AgentReasoningProps {
  evaluation: SafetyEvaluation | null;
}

export const AgentReasoning: React.FC<AgentReasoningProps> = ({ evaluation }) => {
  if (!evaluation) {
    return (
      <div className="card agent-reasoning-container empty">
        <div className="card-header">
          <h3>💬 Safety Council AI Debate</h3>
        </div>
        <div className="reasoning-empty-state">
          <p>Waiting for system telemetry anomaly to initiate multi-agent Safety Council debate...</p>
        </div>
      </div>
    );
  }

  // Get color configurations per agent
  const getAgentStyles = (agentName: string) => {
    switch (agentName) {
      case 'SCADA Agent':
        return { color: '#00f0ff', bg: 'rgba(0, 240, 255, 0.08)', border: '#00f0ff', initials: 'SD' };
      case 'Permit Audit Agent':
        return { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.08)', border: '#f59e0b', initials: 'PA' };
      case 'CCTV Vision Agent':
        return { color: '#ec4899', bg: 'rgba(236, 72, 153, 0.08)', border: '#ec4899', initials: 'CV' };
      case 'Regulatory Compliance Agent':
        return { color: '#a855f7', bg: 'rgba(168, 85, 247, 0.08)', border: '#a855f7', initials: 'RA' };
      case 'Safety Coordinator':
        return { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.08)', border: '#ef4444', initials: 'SC' };
      default:
        return { color: '#9ca3af', bg: 'rgba(156, 163, 175, 0.08)', border: '#9ca3af', initials: 'AI' };
    }
  };

  const score = evaluation.compound_risk_score;
  let scoreColorClass = 'score-safe';
  if (score >= 75) {
    scoreColorClass = 'score-critical';
  } else if (score >= 40) {
    scoreColorClass = 'score-warning';
  }

  return (
    <div className="card agent-reasoning-container">
      <div className="card-header flex-header">
        <div>
          <h3>💬 Safety Council AI Debate</h3>
          <p className="text-small text-muted">{evaluation.explanation}</p>
        </div>
        <div className={`risk-score-circle ${scoreColorClass}`}>
          <div className="score-val">{score}</div>
          <div className="score-lbl">RISK</div>
        </div>
      </div>

      <div className="reasoning-body">
        {/* Debate Transcript */}
        <div className="debate-transcript-section">
          <h4>Council Discussion</h4>
          <div className="debate-scroll">
            {evaluation.debate_transcript.map((msg, i) => {
              const styleObj = getAgentStyles(msg.agent);
              return (
                <div key={i} className="debate-message-bubble" style={{ backgroundColor: styleObj.bg, borderLeft: `3px solid ${styleObj.color}` }}>
                  <div className="message-header">
                    <span className="agent-avatar" style={{ backgroundColor: styleObj.color }}>{styleObj.initials}</span>
                    <span className="agent-name-text" style={{ color: styleObj.color }}>{msg.agent}</span>
                  </div>
                  <p className="message-content-text">{msg.message}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Action checklist and regulations */}
        <div className="mitigation-section">
          <div className="checklist-box">
            <h4>📋 Coordinator Action Checklist</h4>
            <ul className="mitigation-checklist-ui">
              {evaluation.mitigation_checklist.map((step, i) => (
                <li key={i} className="checklist-item">
                  <input type="checkbox" id={`chk-${i}`} defaultChecked={score >= 75 && i === 0} />
                  <label htmlFor={`chk-${i}`}>{step}</label>
                </li>
              ))}
            </ul>
          </div>

          {evaluation.regulatory_citations.length > 0 && (
            <div className="citations-box">
              <h4>⚖️ Regulatory Compliance Audits</h4>
              <div className="citations-list">
                {evaluation.regulatory_citations.map((cite, i) => (
                  <div key={i} className="citation-tag">
                    📖 {cite}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
