import { useState, useEffect, useRef, useCallback } from 'react';

export interface SensorData {
  id: string;
  name: string;
  type: string;
  location: string;
  current_value: number;
  unit: string;
  status: string;
}

export interface WorkerData {
  id: string;
  name: string;
  role: string;
  current_location: string;
  ppe_status: string;
  active_permit_id: string | null;
}

export interface PermitData {
  id: string;
  type: string;
  location: string;
  status: string;
  issued_to: string;
  start_time: string;
  end_time: string;
  hazards_declared: string;
  precautions_taken: string;
}

export interface TelemetryPayload {
  sensors: SensorData[];
  workers: WorkerData[];
  permits: PermitData[];
}

export interface AlertResponse {
  id: string;
  timestamp: string;
  severity: string;
  type: string;
  description: string;
  location: string;
  status: string;
  risk_score: number;
  mitigation_steps: string;
  agent_reasoning_trail: string;
  regulatory_citations: string;
}

export interface DebateMessage {
  agent: string;
  message: string;
}

export interface SafetyEvaluation {
  compound_risk_score: number;
  severity: string;
  explanation: string;
  debate_transcript: DebateMessage[];
  mitigation_checklist: string[];
  regulatory_citations: string[];
  active_alert: {
    id: string;
    status: string;
    location: string;
  } | null;
}

export interface CCTVEvent {
  type: string;
  message: string;
  timestamp: string;
}

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [telemetry, setTelemetry] = useState<TelemetryPayload | null>(null);
  const [safetyEvaluation, setSafetyEvaluation] = useState<SafetyEvaluation | null>(null);
  const [cctvEvents, setCctvEvents] = useState<CCTVEvent[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
    }

    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('Connected to SafeOps AI Telemetry WebSocket');
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'TELEMETRY_UPDATE') {
          setTelemetry(payload.data);
        } else if (payload.type === 'SAFETY_EVALUATION') {
          setSafetyEvaluation(payload.data);
        } else if (payload.type === 'CCTV_EVENT') {
          setCctvEvents((prev) => [payload.data, ...prev.slice(0, 19)]); // Keep last 20 events
        }
      } catch (err) {
        console.error('Error parsing WS frame:', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('SafeOps WebSocket disconnected. Retrying in 3 seconds...');
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket encountered an error:', err);
      ws.close();
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return {
    isConnected,
    telemetry,
    safetyEvaluation,
    cctvEvents,
    clearCctvEvents: () => setCctvEvents([])
  };
}
