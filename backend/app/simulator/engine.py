import asyncio
import random
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Sensor, Worker, Permit, Alert, IncidentReport
from app.api.websockets import manager
from app.agents.coordinator import safety_coordinator

logger = logging.getLogger("safeops")

class SimulatorEngine:
    def __init__(self):
        self.active_scenario: str = "NORMAL"
        self.is_running: bool = False
        self.tick_count: int = 0
        self._task: Optional[asyncio.Task] = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._simulation_loop())
            logger.info("Simulator engine started.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self._task:
                self._task.cancel()
            logger.info("Simulator engine stopped.")

    def set_scenario(self, scenario_id: str):
        self.active_scenario = scenario_id
        self.tick_count = 0
        logger.info(f"Simulator scenario switched to: {scenario_id}")

    async def _simulation_loop(self):
        while self.is_running:
            try:
                await self.tick()
                await asyncio.sleep(2.0)  # Telemetry tick every 2 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in simulator loop: {e}")
                await asyncio.sleep(5.0)

    async def tick(self):
        self.tick_count += 1
        db: Session = SessionLocal()
        try:
            # 1. Simulate Sensors Telemetry
            sensors = db.query(Sensor).all()
            telemetry_data = []
            
            for sensor in sensors:
                old_val = sensor.current_value
                # Apply scenarios or natural fluctuations
                if self.active_scenario == "COKE_OVEN_GAS_LEAK" and sensor.id == "SNS-SEC1-GAS01":
                    # Elevate CO gas rapidly
                    sensor.current_value = min(150.0, old_val + random.uniform(8.0, 15.0))
                elif self.active_scenario == "BOILER_PRESSURE_SPIKE" and sensor.id == "SNS-SEC3-PRESS01":
                    # Elevate steam pressure rapidly
                    sensor.current_value = min(12.0, old_val + random.uniform(0.5, 1.2))
                else:
                    # Natural random walk
                    if sensor.type == "GAS":
                        if sensor.unit == "LEL":
                            sensor.current_value = max(0.0, min(100.0, old_val + random.uniform(-0.5, 0.5)))
                        else:
                            sensor.current_value = max(1.0, min(50.0, old_val + random.uniform(-1.0, 1.0)))
                    elif sensor.type == "TEMP":
                        sensor.current_value = max(20.0, min(120.0, old_val + random.uniform(-0.4, 0.4)))
                    elif sensor.type == "PRESSURE":
                        sensor.current_value = max(1.0, min(10.0, old_val + random.uniform(-0.1, 0.1)))

                # Update Status thresholds
                if sensor.type == "GAS":
                    # Critical thresholds
                    limit = 80.0 if sensor.unit == "LEL" else 35.0
                    warn = 40.0 if sensor.unit == "LEL" else 20.0
                elif sensor.type == "TEMP":
                    limit, warn = 100.0, 80.0
                elif sensor.type == "PRESSURE":
                    limit, warn = 8.5, 7.0
                else:
                    limit, warn = 100.0, 80.0

                if sensor.current_value >= limit:
                    sensor.status = "CRITICAL"
                elif sensor.current_value >= warn:
                    sensor.status = "WARNING"
                else:
                    sensor.status = "NORMAL"
                
                telemetry_data.append({
                    "id": sensor.id,
                    "name": sensor.name,
                    "type": sensor.type,
                    "location": sensor.location,
                    "current_value": round(sensor.current_value, 2),
                    "unit": sensor.unit,
                    "status": sensor.status
                })

            # 2. Simulate Workers movements and PPE violations
            workers = db.query(Worker).all()
            worker_data = []
            cctv_events = []

            for worker in workers:
                # Occasional location changes
                if random.random() < 0.15 and self.active_scenario == "NORMAL":
                    sectors = [
                        "Sector 1 - Coke Oven Battery",
                        "Sector 2 - Storage Tanks",
                        "Sector 4 - Loading Bay"
                    ]
                    old_loc = worker.current_location
                    new_loc = random.choice(sectors)
                    if new_loc != old_loc:
                        worker.current_location = new_loc
                        cctv_events.append({
                            "type": "WORKER_MOVEMENT",
                            "message": f"CCTV detected {worker.name} moved from {old_loc.split(' - ')[0]} to {new_loc.split(' - ')[0]}.",
                            "timestamp": datetime.utcnow().isoformat()
                        })

                # Simulate PPE violation in Scenario B
                if self.active_scenario == "UNAUTHORIZED_CONFINED_ENTRY" and worker.id == "WRK-002":
                    if worker.ppe_status != "MISSING_HELMET":
                        worker.ppe_status = "MISSING_HELMET"
                        cctv_events.append({
                            "type": "PPE_VIOLATION",
                            "message": f"CCTV Alarm: {worker.name} detected in Sector 2 - Storage Tanks without helmet!",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                elif self.active_scenario == "NORMAL" and random.random() < 0.05:
                    # Randomly trigger a temporary PPE violation for demonstration
                    if worker.ppe_status == "FULL":
                        worker.ppe_status = "MISSING_HELMET"
                        cctv_events.append({
                            "type": "PPE_VIOLATION",
                            "message": f"CCTV Alert: {worker.name} detected with missing helmet.",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        worker.ppe_status = "FULL"

                worker_data.append({
                    "id": worker.id,
                    "name": worker.name,
                    "role": worker.role,
                    "current_location": worker.current_location,
                    "ppe_status": worker.ppe_status,
                    "active_permit_id": worker.active_permit_id
                })

            # 3. Simulate Permit Operations
            permits = db.query(Permit).all()
            for permit in permits:
                if self.active_scenario == "COKE_OVEN_GAS_LEAK" and permit.id == "PTW-2026-001":
                    permit.status = "REVOKED"
                elif self.active_scenario == "UNAUTHORIZED_CONFINED_ENTRY" and permit.id == "PTW-2026-002":
                    permit.status = "REVOKED"
                elif self.active_scenario == "NORMAL":
                    permit.status = "APPROVED"

            permit_data = []
            for permit in permits:
                permit_data.append({
                    "id": permit.id,
                    "type": permit.type,
                    "location": permit.location,
                    "status": permit.status,
                    "issued_to": permit.issued_to,
                    "start_time": permit.start_time.isoformat(),
                    "end_time": permit.end_time.isoformat(),
                    "hazards_declared": permit.hazards_declared,
                    "precautions_taken": permit.precautions_taken
                })

            db.commit()

            # --- RUN MULTI-AGENT SAFETY COORDINATOR ---
            sensors_dict = [{
                "id": s.id, "name": s.name, "type": s.type, "location": s.location,
                "current_value": s.current_value, "unit": s.unit, "status": s.status
            } for s in sensors]
            workers_dict = [{
                "id": w.id, "name": w.name, "role": w.role, "current_location": w.current_location,
                "ppe_status": w.ppe_status, "active_permit_id": w.active_permit_id
            } for w in workers]
            permits_dict = [{
                "id": p.id, "type": p.type, "location": p.location, "status": p.status,
                "issued_to": p.issued_to, "start_time": p.start_time, "end_time": p.end_time,
                "hazards_declared": json.loads(p.hazards_declared),
                "precautions_taken": json.loads(p.precautions_taken)
            } for p in permits]

            safety_eval = await safety_coordinator.evaluate_safety(sensors_dict, workers_dict, permits_dict)
            risk_score = safety_eval["compound_risk_score"]
            severity = safety_eval["severity"]

            # Save Alert & IncidentReport to database if risk is high/critical
            active_alert_db = None
            if risk_score >= 40:
                risk_locations = []
                for p in permits_dict:
                    if p["location"] not in risk_locations:
                        risk_locations.append(p["location"])
                loc = risk_locations[0] if risk_locations else "Sector 1 - Coke Oven Battery"
                
                existing_alert = db.query(Alert).filter(
                    Alert.location == loc,
                    Alert.status == "ACTIVE"
                ).first()
                
                if not existing_alert:
                    alert_id = f"ALT-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(100, 999)}"
                    active_alert_db = Alert(
                        id=alert_id,
                        severity=severity,
                        type="COMPOUND_RISK" if risk_score >= 75 else "SINGLE_SENSOR",
                        description=safety_eval["explanation"],
                        location=loc,
                        status="ACTIVE",
                        risk_score=risk_score,
                        mitigation_steps=json.dumps(safety_eval["mitigation_checklist"]),
                        agent_reasoning_trail=json.dumps(safety_eval["debate_transcript"]),
                        regulatory_citations=json.dumps(safety_eval["regulatory_citations"])
                    )
                    db.add(active_alert_db)
                    db.commit()
                    logger.warning(f"New safety alert generated: {alert_id} (Score: {risk_score})")

                    if risk_score >= 75:
                        report_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(100, 999)}"
                        violations = safety_eval["regulatory_citations"]
                        timeline = [
                            {"time": datetime.utcnow().isoformat(), "event": "Compound safety risk detected by SCADA/Permit/Vision sensors."},
                            {"time": datetime.utcnow().isoformat(), "event": "Safety Council debate initiated. Alarm triggered."}
                        ]
                        incident = IncidentReport(
                            id=report_id,
                            alert_id=alert_id,
                            sector=loc.split(" - ")[0],
                            summary=safety_eval["explanation"],
                            timeline=json.dumps(timeline),
                            regulatory_violations=json.dumps(violations),
                            evacuation_status="IN_PROGRESS",
                            authorities_notified=json.dumps(["Plant Fire Chief", "EHS Safety Director"])
                        )
                        db.add(incident)
                        db.commit()
                        logger.warning(f"Incident report generated: {report_id}")
                else:
                    active_alert_db = existing_alert
            else:
                active_alerts = db.query(Alert).filter(Alert.status == "ACTIVE").all()
                for alert in active_alerts:
                    alert.status = "RESOLVED"
                db.commit()

            # 4. Broadcast via WebSocket
            await manager.broadcast({
                "type": "TELEMETRY_UPDATE",
                "timestamp": datetime.utcnow().isoformat(),
                "scenario": self.active_scenario,
                "data": {
                    "sensors": telemetry_data,
                    "workers": worker_data,
                    "permits": permit_data
                }
            })

            # Broadcast Safety Evaluation
            await manager.broadcast({
                "type": "SAFETY_EVALUATION",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "compound_risk_score": risk_score,
                    "severity": severity,
                    "explanation": safety_eval["explanation"],
                    "debate_transcript": safety_eval["debate_transcript"],
                    "mitigation_checklist": safety_eval["mitigation_checklist"],
                    "regulatory_citations": safety_eval["regulatory_citations"],
                    "agent_evaluations": safety_eval["agent_evaluations"],
                    "active_alert": {
                        "id": active_alert_db.id,
                        "status": active_alert_db.status,
                        "location": active_alert_db.location
                    } if active_alert_db else None
                }
            })

            # Broadcast CCTV events if any occurred
            for event in cctv_events:
                await manager.broadcast({
                    "type": "CCTV_EVENT",
                    "timestamp": event["timestamp"],
                    "data": event
                })

        except Exception as e:
            logger.error(f"Simulator tick execution failed: {e}")
            db.rollback()
        finally:
            db.close()

# Global Singleton Simulator Instance
simulator_engine = SimulatorEngine()
