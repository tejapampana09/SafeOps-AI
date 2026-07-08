from typing import List, Dict, Any

class VisionAgent:
    """
    Vision Agent: Analyzes CCTV camera events and worker telemetry.
    Flags PPE breaches, unauthorized entries, and field-level human hazards.
    """
    def __init__(self):
        self.name = "CCTV Vision Agent"

    def analyze(self, workers: List[Dict[str, Any]], permits: List[Dict[str, Any]]) -> Dict[str, Any]:
        risk_score = 0
        confidence_score = 90.0
        findings = []

        active_permits = [p for p in permits if p["status"] == "APPROVED"]

        for worker in workers:
            loc = worker["current_location"]
            ppe = worker["ppe_status"]
            permit_id = worker["active_permit_id"]

            # 1. PPE Breach check
            if ppe != "FULL":
                risk_score = max(risk_score, 60)
                findings.append(f"PPE BREACH: {worker['name']} in {loc} is missing safety gear ({ppe.replace('_', ' ').lower()}).")

            # 2. Confined Space Permit check
            # Sector 2 is high-hazard Confined Space (Storage Tanks)
            if "Sector 2" in loc:
                has_confined_permit = any(p["id"] == permit_id and p["type"] == "CONFINED_SPACE" for p in active_permits)
                if not has_confined_permit:
                    risk_score = max(risk_score, 85)
                    findings.append(f"UNAUTHORIZED ENTRY: {worker['name']} detected in {loc} confined space without an approved Confined Space permit!")
                elif ppe != "FULL":
                    risk_score = max(risk_score, 90)
                    findings.append(f"HIGH DANGER: {worker['name']} in Confined Space ({loc}) with missing safety gear!")

        # Define reasoning
        if risk_score >= 85:
            reasoning = (
                f"Severe field hazard detected. Unauthorized entry into a confined space "
                f"presents immediate worker safety threats. Immediate evacuation is required."
            )
        elif risk_score >= 60:
            reasoning = (
                f"Moderate hazard present due to PPE compliance failures. "
                f"Field supervisors must contact workers to enforce helmet/vest standards."
            )
        else:
            reasoning = "CCTV analytics show full compliance. All workers in active sectors are wearing required PPE, and entry matches approved permits."

        # Define recommended actions
        if risk_score >= 85:
            recommended_actions = [
                "Sound confined space evacuation alarm immediately",
                "Dispatch safety standby supervisor to Sector 2 entry point",
                "Ensure emergency rescue harness and oxygen is standby"
            ]
        elif risk_score >= 60:
            recommended_actions = [
                "Instruct worker via sector intercom to wear required PPE",
                "Report PPE safety violation to site supervisor"
            ]
        else:
            recommended_actions = [
                "Maintain continuous CCTV video analytics surveillance"
            ]

        return {
            "agent": self.name,
            "risk_score": risk_score,
            "confidence_score": confidence_score,
            "findings": findings,
            "reasoning": reasoning,
            "recommended_actions": recommended_actions
        }
