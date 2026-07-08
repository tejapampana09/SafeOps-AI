import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import Sensor, Worker, Permit, Alert, IncidentReport
from app.schemas import (
    SensorResponse, WorkerResponse, PermitResponse, PermitCreate, 
    AlertResponse, AlertUpdate, IncidentReportResponse, SimulationTrigger, QueryRequest
)
from app.api.websockets import manager

router = APIRouter()

@router.get("/state", response_model=Dict[str, Any])
def get_plant_state(db: Session = Depends(get_db)):
    """Returns the comprehensive state of the industrial plant."""
    try:
        sensors = db.query(Sensor).all()
        workers = db.query(Worker).all()
        permits = db.query(Permit).all()
        active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").all()
        
        return {
            "sensors": [SensorResponse.model_validate(s) for s in sensors],
            "workers": [WorkerResponse.model_validate(w) for w in workers],
            "permits": [PermitResponse.model_validate(p) for p in permits],
            "alerts": [AlertResponse.model_validate(a) for a in active_alerts]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database state retrieval failed: {e}"
        )

@router.post("/permits/create", response_model=PermitResponse)
def create_permit(permit_in: PermitCreate, db: Session = Depends(get_db)):
    """Issues a new Digital Permit-to-Work."""
    existing = db.query(Permit).filter(Permit.id == permit_in.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permit ID already exists"
        )
    
    new_permit = Permit(
        id=permit_in.id,
        type=permit_in.type,
        location=permit_in.location,
        status="APPROVED",
        issued_to=permit_in.issued_to,
        start_time=permit_in.start_time,
        end_time=permit_in.end_time,
        hazards_declared=json.dumps(permit_in.hazards_declared),
        precautions_taken=json.dumps(permit_in.precautions_taken)
    )
    db.add(new_permit)
    db.commit()
    db.refresh(new_permit)
    return new_permit

@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """Acknowledges an active alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    alert.status = "ACKNOWLEDGED"
    db.commit()
    db.refresh(alert)
    return alert

@router.get("/alerts/history", response_model=List[AlertResponse])
def get_alert_history(db: Session = Depends(get_db)):
    """Retrieves all generated safety alerts."""
    return db.query(Alert).order_by(Alert.timestamp.desc()).all()

@router.get("/alerts/{alert_id}/report", response_model=IncidentReportResponse)
def get_incident_report(alert_id: str, db: Session = Depends(get_db)):
    """Generates and retrieves the formal incident report for a specific safety breach."""
    report = db.query(IncidentReport).filter(IncidentReport.alert_id == alert_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No incident report found for this alert ID."
        )
    return report

from app.simulator.engine import simulator_engine

@router.post("/simulator/trigger")
async def trigger_simulation(trigger: SimulationTrigger):
    """Triggers an industrial hazard scenario (e.g., Coke Oven Leak)."""
    if trigger.scenario_id not in ["NORMAL", "GAS_LEAK", "HOT_WORK_CONFLICT", "UNAUTHORIZED_WORKER", "COMBINED_COMPOUND_RISK"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario ID '{trigger.scenario_id}'. Available: NORMAL, GAS_LEAK, HOT_WORK_CONFLICT, UNAUTHORIZED_WORKER, COMBINED_COMPOUND_RISK"
        )
    
    simulator_engine.set_scenario(trigger.scenario_id)
    await manager.broadcast({
        "type": "SIMULATION_TRIGGERED",
        "scenario_id": trigger.scenario_id
    })
    return {"status": "SUCCESS", "message": f"Simulation scenario '{trigger.scenario_id}' activated."}

@router.post("/rag/query")
def regulatory_query(query: QueryRequest):
    """RAG engine query endpoint for OISD and Factory Act standards."""
    # Note: RAG response will interface with Gemini LLM in Phase 4
    return {
        "query": query.query,
        "response": "Under Section 36 of the Factories Act 1948, entry into any confined space is prohibited unless a written permit is issued and appropriate gas testing has confirmed the absence of toxic gas concentrations.",
        "citations": ["Factories Act 1948 - Section 36", "OISD-GDN-115 Section 4.2"]
    }
