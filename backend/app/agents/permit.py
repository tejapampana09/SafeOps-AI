from typing import List, Dict, Any

class PermitAgent:
    """
    Permit Agent: Audits active digital Permits-to-Work against plant state.
    Identifies hazardous SimOps (Simultaneous Operations) and permit rule breaches.
    """
    def __init__(self):
        self.name = "Permit Audit Agent"

    def analyze(self, permits: List[Dict[str, Any]], sensors: List[Dict[str, Any]]) -> Dict[str, Any]:
        risk_score = 0
        confidence_score = 98.0
        findings = []
        
        # Check active permits count
        active_permits = [p for p in permits if p["status"] == "APPROVED"]
        
        # Map location to active permits
        loc_permits: Dict[str, List[Dict[str, Any]]] = {}
        for p in active_permits:
            loc = p["location"]
            loc_permits.setdefault(loc, []).append(p)
        
        # Check for SimOps conflicts (multiple active permits in same sector)
        for loc, p_list in loc_permits.items():
            if len(p_list) > 1:
                types = [p["type"] for p in p_list]
                # Severe conflict: HOT_WORK + CONFINED_SPACE or HOT_WORK + chemical risk
                if "HOT_WORK" in types:
                    risk_score = max(risk_score, 75)
                    findings.append(f"SIMOPS CONFLICT: Multiple active permits in {loc} including HOT_WORK: {', '.join(types)}.")
                else:
                    risk_score = max(risk_score, 40)
                    findings.append(f"SimOps warning: Multiple active permits in {loc}: {', '.join(types)}.")

        # Check for Hot Work / Confined Space near elevated Gas sensors
        for p in active_permits:
            loc = p["location"]
            # Find sensors in the same location
            local_sensors = [s for s in sensors if s["location"].startswith(loc.split(" - ")[0])]
            
            for s in local_sensors:
                if s["type"] == "GAS" and s["status"] != "NORMAL":
                    if p["type"] == "HOT_WORK":
                        risk_score = max(risk_score, 85)
                        findings.append(
                            f"PERMIT VIOLATION: Hot Work permit {p['id']} active in {loc} "
                            f"with elevated gas reading ({s['current_value']}{s['unit']}) on {s['id']}."
                        )
                    elif p["type"] == "CONFINED_SPACE":
                        risk_score = max(risk_score, 80)
                        findings.append(
                            f"PERMIT HAZARD: Confined Space permit {p['id']} active in {loc} "
                            f"with elevated toxic/flammable gas ({s['current_value']}{s['unit']}) on {s['id']}."
                        )

        # Define reasoning
        if risk_score >= 75:
            reasoning = (
                f"Severe permit compliance risk detected. SimOps conflict or active hot work "
                f"near gas anomalies poses an immediate explosion/ignition hazard. "
                f"Affected permits must be revoked immediately."
            )
        elif risk_score >= 40:
            reasoning = (
                "Moderate risk. Multiple permits are active in the same sector. "
                "Coordinated safety protocols must be verified to prevent cross-activity hazards."
            )
        else:
            reasoning = f"Permit compliance is normal. No SimOps conflicts or hazardous hot work overlaps detected. Active permits: {len(active_permits)}."

        return {
            "agent": self.name,
            "risk_score": risk_score,
            "confidence_score": confidence_score,
            "findings": findings,
            "reasoning": reasoning
        }
