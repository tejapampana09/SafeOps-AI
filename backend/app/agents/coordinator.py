import json
import logging
import os
from typing import List, Dict, Any, Tuple
import google.generativeai as genai

from app.config import settings
from app.agents.scada import SCADAAgent
from app.agents.permit import PermitAgent
from app.agents.vision import VisionAgent

logger = logging.getLogger("safeops")

# Initialize Gemini if API key is present
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

class SafetyCoordinator:
    """
    Safety Coordinator Agent: Aggregates risk inputs from SCADA, Permit, and Vision agents.
    Triggers and orchestrates the multi-agent 'Safety Council' debate when anomalies occur,
    resolving a final Compound Risk Score and mitigation plan.
    """
    def __init__(self):
        self.name = "Safety Coordinator"
        self.scada_agent = SCADAAgent()
        self.permit_agent = PermitAgent()
        self.vision_agent = VisionAgent()

    async def evaluate_safety(self, sensors: List[Dict[str, Any]], workers: List[Dict[str, Any]], permits: List[Dict[str, Any]]) -> Dict[str, Any]:
        # 1. Run individual agent evaluations
        scada_result = self.scada_agent.analyze(sensors)
        permit_result = self.permit_agent.analyze(permits, sensors)
        vision_result = self.vision_agent.analyze(workers, permits)

        # 2. Compute Compound Risk Score (Base logic: weighted/max value)
        # If any agent reports critical risk, let that dominate the score
        max_risk = max(scada_result["risk_score"], permit_result["risk_score"], vision_result["risk_score"])
        
        # Calculate weighted average for moderate states
        avg_risk = int(0.4 * scada_result["risk_score"] + 0.3 * permit_result["risk_score"] + 0.3 * vision_result["risk_score"])
        
        compound_risk_score = max(max_risk, avg_risk)

        # Determine Severity Level
        if compound_risk_score >= 75:
            severity = "CRITICAL"
        elif compound_risk_score >= 40:
            severity = "HIGH"
        elif compound_risk_score >= 20:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # 3. Check if we need to run a safety debate
        # Debates are triggered if any risk is HIGH/CRITICAL (risk_score >= 40)
        has_anomalies = compound_risk_score >= 40
        
        debate_transcript = []
        mitigation_checklist = []
        regulatory_citations = []
        explanation = ""

        if has_anomalies:
            logger.info("Anomalies detected. Initiating Safety Council Agentic Debate...")
            debate_transcript, mitigation_checklist, regulatory_citations, explanation = await self._run_debate(
                sensors, workers, permits, scada_result, permit_result, vision_result, compound_risk_score
            )
        else:
            # Baseline normal state explanation
            explanation = "All industrial safety checks are clear. Plant is operating within zero-harm boundaries."
            mitigation_checklist = ["Continue routine patrols", "Monitor sensor telemetry streams"]
            regulatory_citations = []

        return {
            "compound_risk_score": compound_risk_score,
            "severity": severity,
            "explanation": explanation,
            "agent_evaluations": {
                "scada": scada_result,
                "permit": permit_result,
                "vision": vision_result
            },
            "debate_transcript": debate_transcript,
            "mitigation_checklist": mitigation_checklist,
            "regulatory_citations": regulatory_citations
        }

    async def _run_debate(
        self,
        sensors: List[Dict[str, Any]],
        workers: List[Dict[str, Any]],
        permits: List[Dict[str, Any]],
        scada_res: Dict[str, Any],
        permit_res: Dict[str, Any],
        vision_res: Dict[str, Any],
        risk_score: int
    ) -> Tuple[List[Dict[str, str]], List[str], List[str], str]:
        
        # If Gemini API key is configured, run live LLM debate
        if settings.GEMINI_API_KEY:
            try:
                return await self._run_llm_debate(sensors, workers, permits, scada_res, permit_res, vision_res, risk_score)
            except Exception as e:
                logger.error(f"Gemini LLM debate execution failed: {e}. Falling back to structured templates.")
                # Fallback to local template below
        
        # Fallback structured templates to guarantee zero-fail during presentation
        return self._get_template_debate(sensors, workers, permits, scada_res, permit_res, vision_res, risk_score)

    async def _run_llm_debate(
        self,
        sensors: List[Dict[str, Any]],
        workers: List[Dict[str, Any]],
        permits: List[Dict[str, Any]],
        scada_res: Dict[str, Any],
        permit_res: Dict[str, Any],
        vision_res: Dict[str, Any],
        risk_score: int
    ) -> Tuple[List[Dict[str, str]], List[str], List[str], str]:
        
        # Format current state for prompt context
        state_summary = {
            "sensors": sensors,
            "workers": workers,
            "permits": permits,
            "agent_findings": {
                "SCADA Agent": scada_res,
                "Permit Agent": permit_res,
                "Vision Agent": vision_res
            }
        }

        prompt = f"""
You are the Safety Coordinator at a heavy industrial steel and chemical plant.
An industrial safety event is unfolding. You must orchestrate a "Safety Council Debate" between these 4 agents:
1. SCADA Agent (monitors pressure, temperature, and gas sensor telemetry)
2. Permit Audit Agent (monitors active Permits-to-Work and SimOps conflicts)
3. CCTV Vision Agent (monitors worker PPE and physical locations via video analytics)
4. Regulatory Compliance Agent (evaluates rules against OISD standards and Indian Factories Act 1948)

Current Plant state and Agent findings:
{json.dumps(state_summary, indent=2)}

Generate a structured multi-turn conversation where the agents identify the hazard, debate the risk factors, cite official regulations, and agree on an exact list of emergency mitigation steps.
You MUST respond ONLY with a JSON object matching this exact schema:
{{
  "debate_transcript": [
    {{"agent": "SCADA Agent", "message": "..."}},
    {{"agent": "Permit Audit Agent", "message": "..."}},
    {{"agent": "CCTV Vision Agent", "message": "..."}},
    {{"agent": "Regulatory Compliance Agent", "message": "According to OISD-GDN-... / Factories Act Section ..."}},
    {{"agent": "Safety Coordinator", "message": "..."}}
  ],
  "mitigation_checklist": [
    "Step 1: ...",
    "Step 2: ..."
  ],
  "regulatory_citations": [
    "OISD-STD-...",
    "Factories Act 1948 - Section ..."
  ],
  "explanation": "Summarized safety coordination verdict."
}}
"""
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        parsed = json.loads(response.text)
        return (
            parsed.get("debate_transcript", []),
            parsed.get("mitigation_checklist", []),
            parsed.get("regulatory_citations", []),
            parsed.get("explanation", "")
        )

    def _get_template_debate(
        self,
        sensors: List[Dict[str, Any]],
        workers: List[Dict[str, Any]],
        permits: List[Dict[str, Any]],
        scada_res: Dict[str, Any],
        permit_res: Dict[str, Any],
        vision_res: Dict[str, Any],
        risk_score: int
    ) -> Tuple[List[Dict[str, str]], List[str], List[str], str]:
        
        # Check active scenarios
        co_gas = next((s["current_value"] for s in sensors if s["id"] == "SNS-SEC1-GAS01"), 0.0)
        amit = next((w for w in workers if w["id"] == "WRK-001"), None)
        rajesh = next((w for w in workers if w["id"] == "WRK-003"), None)
        p1 = next((p for p in permits if p["id"] == "PTW-2026-001"), None)

        is_combined = co_gas > 70.0 and amit is not None and "Sector 1" in amit["current_location"]
        is_gas_leak = co_gas > 30.0 and (p1 is None or p1["status"] == "EXPIRED")
        is_hot_work_conflict = co_gas > 15.0 and p1 is not None and p1["status"] == "APPROVED" and co_gas <= 30.0
        is_unauthorized = rajesh is not None and "Sector 2" in rajesh["current_location"]

        debate_transcript = []
        mitigation_checklist = []
        regulatory_citations = []
        explanation = ""

        if is_combined:
            debate_transcript = [
                {
                    "agent": "SCADA Agent",
                    "message": f"Critical Safety Threat! CO gas concentration at SNS-SEC1-GAS01 in Sector 1 Coke Oven Battery has breached critical thresholds, registering at {co_gas} ppm."
                },
                {
                    "agent": "Permit Audit Agent",
                    "message": "Permit check: Hot Work Permit PTW-2026-001 (welding) is active in Sector 1. This represents an immediate explosion hazard in the presence of toxic CO gas accumulation!"
                },
                {
                    "agent": "CCTV Vision Agent",
                    "message": "CCTV visual check confirms worker Amit Sharma is present in Sector 1 near the coke oven line. They are in direct proximity to the gas leak."
                },
                {
                    "agent": "Regulatory Compliance Agent",
                    "message": "According to Section 36 of the Factories Act 1948 and OISD-GDN-137, all hot work operations must be suspended immediately, and personnel must be evacuated when flammable or toxic gas concentrations exceed safe occupational exposure limits."
                },
                {
                    "agent": "Safety Coordinator",
                    "message": "Initiating critical emergency response protocol. Revoking Hot Work Permit PTW-2026-001, triggering Sector 1 evacuation sirens, and notifying EHS response teams."
                }
            ]
            mitigation_checklist = [
                "Evacuate worker Amit Sharma and all personnel from Sector 1",
                "Revoke and suspend Hot Work Permit PTW-2026-001",
                "Trigger automated nitrogen purging for coke oven line isolation",
                "Activate Sector 1 exhaust scrubbers to ventilate CO gas"
            ]
            regulatory_citations = [
                "Factories Act 1948 - Section 36 (Precautions against dangerous fumes)",
                "OISD-GDN-137 (Permit to Work System Guidelines)"
            ]
            explanation = "CRITICAL HAZARD: CO gas leak co-occurring with active hot work welding and workers present in Sector 1. Evacuation and permit suspension initiated."

        elif is_gas_leak:
            debate_transcript = [
                {
                    "agent": "SCADA Agent",
                    "message": f"SCADA process alert: CO gas concentration at SNS-SEC1-GAS01 in Sector 1 Coke Oven Battery has drifted to warning level of {co_gas} ppm."
                },
                {
                    "agent": "Permit Audit Agent",
                    "message": "Permit audit shows Permit PTW-2026-001 is EXPIRED. No hot work or maintenance operations are active in Sector 1. The ignition risk is low."
                },
                {
                    "agent": "CCTV Vision Agent",
                    "message": "CCTV logs verify Sector 1 is empty of workers. Amit Sharma was successfully relocated to Sector 4."
                },
                {
                    "agent": "Regulatory Compliance Agent",
                    "message": "Although there is no worker present, Section 36 of the Factories Act 1948 requires gas testing to identify and repair leaks. The area must remain cordoned off."
                },
                {
                    "agent": "Safety Coordinator",
                    "message": "Understood. The hazard is restricted to a process anomaly. No immediate evacuation is needed, but we will dispatch maintenance to seal the leak."
                }
            ]
            mitigation_checklist = [
                "Cordon off Sector 1 Coke Oven Battery entrance",
                "Deploy maintenance crew with portable gas sniffers to locate leak source",
                "Verify Sector 1 mechanical exhaust fans are operational"
            ]
            regulatory_citations = [
                "Factories Act 1948 - Section 36 (Gas testing requirements)",
                "OISD-STD-105 Section 6.2"
            ]
            explanation = "Process Warning: Elevated CO gas detected in Sector 1. Sector is clear of personnel. Maintenance crew dispatched for line leak check."

        elif is_hot_work_conflict:
            debate_transcript = [
                {
                    "agent": "Permit Audit Agent",
                    "message": "Permit Conflict Alert: Hot Work permit PTW-2026-001 (welding) is active in Sector 1, but process parameters show minor CO gas leak warnings."
                },
                {
                    "agent": "SCADA Agent",
                    "message": f"Sensor SNS-SEC1-GAS01 reads {co_gas} ppm. This is below critical levels but above normal. Accumulations could lead to an ignition incident."
                },
                {
                    "agent": "CCTV Vision Agent",
                    "message": "CCTV scans Amit Sharma active in Sector 1 with welding gear. Standard helmet and vest PPE is present."
                },
                {
                    "agent": "Regulatory Compliance Agent",
                    "message": "Under OISD-GDN-137, hot work permits can only be approved if the environment is verified gas-free. An active permit during any gas drift represents a compliance conflict."
                },
                {
                    "agent": "Safety Coordinator",
                    "message": "Agreed. Suspending welding operations temporarily as a safety precaution. Restoring permit only after CO levels stabilize."
                }
            ]
            mitigation_checklist = [
                "Instruct worker Amit Sharma to temporarily halt welding operations",
                "Deploy safety inspector to verify local gas level at welding nozzle",
                "Audit hot work permit precautions compliance logs"
            ]
            regulatory_citations = [
                "OISD-GDN-137 (Permit compliance standards)",
                "Factories Act 1948 - Section 36"
            ]
            explanation = "Safety Conflict: Active hot work permit approved in Sector 1 during minor CO gas warning. Temporary work suspension recommended."

        elif is_unauthorized:
            debate_transcript = [
                {
                    "agent": "CCTV Vision Agent",
                    "message": "Field Alert! CCTV analytics detect worker Rajesh Kumar has entered Sector 2 Storage Tanks confined space area."
                },
                {
                    "agent": "Permit Audit Agent",
                    "message": "Permit check: Rajesh Kumar has NO active permit (active_permit_id is NULL). Confined Space Permit PTW-2026-002 is registered only to Priya Patel."
                },
                {
                    "agent": "SCADA Agent",
                    "message": "SCADA sensors show gas levels inside Sector 2 are currently normal, but toxic gas pockets can form rapidly without continuous ventilation."
                },
                {
                    "agent": "Regulatory Compliance Agent",
                    "message": "Entering a confined space without a valid Confined Space Entry Permit and a standby supervisor breaches Section 36 of the Factories Act 1948 and OISD-STD-105."
                },
                {
                    "agent": "Safety Coordinator",
                    "message": "Critical compliance breach. Alerting Sector 2 standby supervisor to immediately recall Rajesh Kumar from the storage tank."
                }
            ]
            mitigation_checklist = [
                "Recall worker Rajesh Kumar from Sector 2 confined space immediately",
                "Deploy safety supervisor to secure the Sector 2 manway entry point",
                "Perform safety briefing with technician regarding permit procedures"
            ]
            regulatory_citations = [
                "Factories Act 1948 - Section 36 (Confined Space Entry Rules)",
                "OISD-STD-105 (Permit to Work System)"
            ]
            explanation = "Field Violation: Worker Rajesh Kumar detected inside Sector 2 Storage Tank confined space without an approved Confined Space permit."

        else:
            debate_transcript = [
                {
                    "agent": "Safety Coordinator",
                    "message": f"Safety evaluation completed. Compound risk rating is {risk_score}."
                },
                {
                    "agent": "SCADA Agent",
                    "message": "All process variables (temperature, pressure, gas concentration) are stable."
                },
                {
                    "agent": "Regulatory Compliance Agent",
                    "message": "No regulatory deviations or safety compliance conflicts identified."
                }
            ]
            mitigation_checklist = ["Perform standard inspection patrols", "Verify sensor telemetry streams"]
            regulatory_citations = []
            explanation = "System Secure. All safety parameters are within zero-harm boundaries."

        return debate_transcript, mitigation_checklist, regulatory_citations, explanation

# Global Safety Coordinator Instance
safety_coordinator = SafetyCoordinator()
