# SafeOps AI - Industrial Safety Intelligence for Zero-Harm Operations

SafeOps AI is a real-time, multi-agent safety intelligence platform built to satisfy Problem Statement 1 of the ET AI Hackathon 2026. It integrates SCADA sensor telemetry, digital work permits, and visual safety event streams into a unified hazard assessment layer.

## Project Structure
```
hackathon/
├── backend/                  # FastAPI & AI Agents
│   ├── app/
│   │   ├── api/              # API endpoints and WS gateways
│   │   ├── agents/           # SCADA, Permit, Vision and Coordinator Agents
│   │   ├── simulator/        # Telemetry & event simulation engine
│   │   ├── database.py       # SQLite connection setup
│   │   ├── models.py         # SQLAlchemy data schemas
│   │   └── main.py           # FastAPI entrypoint
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React & Vite control cockpit
│   ├── src/
│   │   ├── components/       # Visual control room components
│   │   ├── hooks/            # WebSockets client hooks
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml        # Orchestration layer
└── README.md
```

## Running the Application

### Option 1: Docker Compose (Recommended)
Run the following command at the root directory:
```bash
docker-compose up --build
```
* **Frontend Cockpit:** http://localhost:5173
* **FastAPI Server:** http://localhost:8000

### Option 2: Local Execution
#### 1. Backend:
```bash
cd backend
python -m venv venv
./venv/Scripts/activate # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 2. Frontend:
```bash
cd frontend
npm install
npm run dev
```
