import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # GAS, TEMP, PRESSURE, FLOW
    location = Column(String, nullable=False)  # Sector 1, Sector 2, etc.
    current_value = Column(Float, default=0.0)
    unit = Column(String, nullable=False)  # ppm, LEL, C, bar
    status = Column(String, default="NORMAL")  # NORMAL, WARNING, CRITICAL

class Permit(Base):
    __tablename__ = "permits"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, nullable=False)  # HOT_WORK, CONFINED_SPACE, ELECTRICAL, COLD_WORK
    location = Column(String, nullable=False)  # Sector name
    status = Column(String, default="APPROVED")  # APPROVED, PENDING, EXPIRED, REVOKED
    issued_to = Column(String, nullable=False)  # Maintenance Team A
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=False)
    hazards_declared = Column(Text, default="[]")  # JSON string list
    precautions_taken = Column(Text, default="[]")  # JSON string list

    workers = relationship("Worker", back_populates="permit")

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    current_location = Column(String, nullable=False)
    ppe_status = Column(String, default="FULL")  # FULL, MISSING_HELMET, MISSING_VEST, NONE
    active_permit_id = Column(String, ForeignKey("permits.id"), nullable=True)

    permit = relationship("Permit", back_populates="workers")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    type = Column(String, nullable=False)  # SINGLE_SENSOR, COMPOUND_RISK, REGULATORY_BREACH
    description = Column(Text, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")  # ACTIVE, ACKNOWLEDGED, RESOLVED
    risk_score = Column(Integer, default=0)  # 0-100
    mitigation_steps = Column(Text, default="[]")  # JSON string list of actions
    agent_reasoning_trail = Column(Text, default="[]")  # JSON string log of agent debate
    regulatory_citations = Column(Text, default="[]")  # JSON string list of citations

    incident_reports = relationship("IncidentReport", back_populates="alert")

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(String, primary_key=True, index=True)
    alert_id = Column(String, ForeignKey("alerts.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    sector = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    timeline = Column(Text, default="[]")  # JSON timeline events
    regulatory_violations = Column(Text, default="[]")  # JSON violations
    evacuation_status = Column(String, default="NONE")  # NONE, IN_PROGRESS, COMPLETED
    authorities_notified = Column(Text, default="[]")  # JSON notification details

    alert = relationship("Alert", back_populates="incident_reports")
