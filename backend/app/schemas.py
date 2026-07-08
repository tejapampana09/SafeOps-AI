from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Sensor Schemas ---
class SensorBase(BaseModel):
    id: str
    name: str
    type: str
    location: str
    current_value: float
    unit: str
    status: str

class SensorUpdate(BaseModel):
    current_value: float
    status: str

class SensorResponse(SensorBase):
    class Config:
        from_attributes = True

# --- Worker Schemas ---
class WorkerBase(BaseModel):
    id: str
    name: str
    role: str
    current_location: str
    ppe_status: str
    active_permit_id: Optional[str] = None

class WorkerUpdate(BaseModel):
    current_location: str
    ppe_status: str
    active_permit_id: Optional[str] = None

class WorkerResponse(WorkerBase):
    class Config:
        from_attributes = True

# --- Permit Schemas ---
class PermitBase(BaseModel):
    id: str
    type: str
    location: str
    status: str
    issued_to: str
    start_time: datetime
    end_time: datetime
    hazards_declared: str  # JSON list
    precautions_taken: str  # JSON list

class PermitCreate(BaseModel):
    id: str
    type: str
    location: str
    issued_to: str
    start_time: datetime
    end_time: datetime
    hazards_declared: List[str]
    precautions_taken: List[str]

class PermitResponse(BaseModel):
    id: str
    type: str
    location: str
    status: str
    issued_to: str
    start_time: datetime
    end_time: datetime
    hazards_declared: str
    precautions_taken: str
    workers: List[WorkerResponse] = []

    class Config:
        from_attributes = True

# --- Alert Schemas ---
class AlertBase(BaseModel):
    id: str
    timestamp: datetime
    severity: str
    type: str
    description: str
    location: str
    status: str
    risk_score: int
    mitigation_steps: str  # JSON list
    agent_reasoning_trail: str  # JSON log
    regulatory_citations: str  # JSON list

class AlertUpdate(BaseModel):
    status: str

class AlertResponse(AlertBase):
    class Config:
        from_attributes = True

# --- Incident Report Schemas ---
class IncidentReportBase(BaseModel):
    id: str
    alert_id: str
    timestamp: datetime
    sector: str
    summary: str
    timeline: str  # JSON list
    regulatory_violations: str  # JSON list
    evacuation_status: str
    authorities_notified: str  # JSON list

class IncidentReportResponse(IncidentReportBase):
    alert: AlertResponse

    class Config:
        from_attributes = True

# --- API Interaction Schemas ---
class SimulationTrigger(BaseModel):
    scenario_id: str

class QueryRequest(BaseModel):
    query: str

class AlertAcknowledge(BaseModel):
    alert_id: str
