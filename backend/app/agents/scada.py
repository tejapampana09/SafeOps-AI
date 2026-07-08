from typing import List, Dict, Any

class SCADAAgent:
    """
    SCADA Agent: Monitors industrial telemetry sensors (gas, pressure, temp).
    Evaluates physical thresholds and trends to compute a safety risk score.
    """
    def __init__(self):
        self.name = "SCADA Agent"

    def analyze(self, sensors: List[Dict[str, Any]]) -> Dict[str, Any]:
        risk_score = 0
        confidence_score = 95.0
        findings = []
        critical_sensors = []
        warning_sensors = []

        for sensor in sensors:
            val = sensor["current_value"]
            status = sensor["status"]
            loc = sensor["location"]
            
            if status == "CRITICAL":
                critical_sensors.append(sensor)
                findings.append(f"CRITICAL reading: {sensor['name']} at {val}{sensor['unit']} in {loc}")
            elif status == "WARNING":
                warning_sensors.append(sensor)
                findings.append(f"WARNING reading: {sensor['name']} at {val}{sensor['unit']} in {loc}")

        # Compute risk score based on sensor statuses
        if critical_sensors:
            # High risk if any sensor is critical
            risk_score = min(100, 70 + len(critical_sensors) * 10)
        elif warning_sensors:
            risk_score = min(69, 30 + len(warning_sensors) * 8)
        else:
            # Baseline normal fluctuations
            risk_score = max(5, int(sum(s["current_value"] for s in sensors if s["type"] == "GAS") / len(sensors)))

        # Define reasoning
        if critical_sensors:
            reasoning = (
                f"Severe risk detected. Multiple process parameters are breached. "
                f"Critical values registered at {', '.join([s['id'] for s in critical_sensors])}. "
                f"Immediate containment or shutdown is required."
            )
        elif warning_sensors:
            reasoning = (
                f"Elevated risk present. Parameters starting to drift outside normal limits. "
                f"Warnings registered on {', '.join([s['id'] for s in warning_sensors])}. "
                f"Needs close monitoring."
            )
        else:
            reasoning = "All process parameters (gas, temp, pressure) are within normal operating bounds. No immediate process hazards identified."

        return {
            "agent": self.name,
            "risk_score": risk_score,
            "confidence_score": confidence_score,
            "findings": findings,
            "reasoning": reasoning
        }
