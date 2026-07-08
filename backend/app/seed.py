import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Sensor, Worker, Permit, Alert
from app.database import SessionLocal, engine, Base

def seed_database(db: Session):
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)

    # 1. Seed Sensors
    if db.query(Sensor).count() == 0:
        sensors = [
            Sensor(
                id="SNS-SEC1-GAS01",
                name="CO Gas Detector (Sector 1)",
                type="GAS",
                location="Sector 1 - Coke Oven Battery",
                current_value=12.5,
                unit="ppm",
                status="NORMAL"
            ),
            Sensor(
                id="SNS-SEC1-TEMP01",
                name="Thermal Gas Probe (Sector 1)",
                type="TEMP",
                location="Sector 1 - Coke Oven Battery",
                current_value=85.0,
                unit="C",
                status="NORMAL"
            ),
            Sensor(
                id="SNS-SEC2-GAS01",
                name="Methane Gas Detector (Sector 2)",
                type="GAS",
                location="Sector 2 - Storage Tanks",
                current_value=0.0,
                unit="LEL",
                status="NORMAL"
            ),
            Sensor(
                id="SNS-SEC3-PRESS01",
                name="Steam Boiler Pressure (Sector 3)",
                type="PRESSURE",
                location="Sector 3 - Utility Block",
                current_value=6.2,
                unit="bar",
                status="NORMAL"
            ),
            Sensor(
                id="SNS-SEC4-GAS01",
                name="Ammonia Sensor (Sector 4)",
                type="GAS",
                location="Sector 4 - Loading Bay",
                current_value=5.0,
                unit="ppm",
                status="NORMAL"
            ),
        ]
        db.add_all(sensors)
        db.commit()
        print("Seeded sensors successfully.")

    # 2. Seed Permits
    if db.query(Permit).count() == 0:
        permits = [
            Permit(
                id="PTW-2026-001",
                type="HOT_WORK",
                location="Sector 1 - Coke Oven Battery",
                status="APPROVED",
                issued_to="Mechanical Maintenance A",
                start_time=datetime.utcnow() - timedelta(hours=2),
                end_time=datetime.utcnow() + timedelta(hours=6),
                hazards_declared=json.dumps(["Flame exposure", "Elevated heat", "Sparks"]),
                precautions_taken=json.dumps(["Fire extinguisher standby", "Gas testing prior", "Shielding screens"])
            ),
            Permit(
                id="PTW-2026-002",
                type="CONFINED_SPACE",
                location="Sector 2 - Storage Tanks",
                status="APPROVED",
                issued_to="Tank Inspection Group",
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow() + timedelta(hours=4),
                hazards_declared=json.dumps(["Oxygen deficiency", "Toxic gas accumulation"]),
                precautions_taken=json.dumps(["LOTO verification", "Continuous ventilation", "Safety harness & lifeline"])
            )
        ]
        db.add_all(permits)
        db.commit()
        print("Seeded permits successfully.")

    # 3. Seed Workers
    if db.query(Worker).count() == 0:
        workers = [
            Worker(
                id="WRK-001",
                name="Amit Sharma",
                role="Technician",
                current_location="Sector 1 - Coke Oven Battery",
                ppe_status="FULL",
                active_permit_id="PTW-2026-001"
            ),
            Worker(
                id="WRK-002",
                name="Priya Patel",
                role="Maintenance Engineer",
                current_location="Sector 2 - Storage Tanks",
                ppe_status="FULL",
                active_permit_id="PTW-2026-002"
            ),
            Worker(
                id="WRK-003",
                name="Rajesh Kumar",
                role="Safety Inspector",
                current_location="Sector 4 - Loading Bay",
                ppe_status="FULL",
                active_permit_id=None
            )
        ]
        db.add_all(workers)
        db.commit()
        print("Seeded workers successfully.")
