# SafeOps AI - Industrial Safety Intelligence for Zero-Harm Operations

SafeOps AI is a production-ready, multi-agent safety intelligence platform designed for heavy industrial environments (such as steel plants, chemical refineries, and mining facilities). It addresses the critical information fragmentation bottleneck in industrial safety operations by unifying SCADA sensor telemetry, digital work permits, and visual CCTV analytics into a real-time predictive risk engine.

SafeOps AI was built as a hackathon-winning submission for **Problem Statement 1 (AI-Powered Industrial Safety Intelligence for Zero-Harm Operations)** in the **ET AI Hackathon 2026**.

---

## 🏗️ System & AI Architecture

### 1. Architecture Diagram
```mermaid
graph TD
    subgraph Data Feeds & Simulation Gateway
        IoT[IoT / Gas Sensors Simulator] -->|JSON/WebSockets| Ingest[FastAPI Ingestion Gateway]
        SCADA[SCADA System Logs] -->|JSON/WebSockets| Ingest
        PTW[Permit-to-Work DB] -->|SQLite Queries| Ingest
        CCTV[CCTV Video Analytics] -->|Event Stream| Ingest
    end

    subgraph Core AI & Agents Layer (FastAPI)
        Ingest -->|Stream| StreamProcessor[Stream Coordinator]
        StreamProcessor -->|State DB Commit| SQLite[(SQLite: State & Logs)]
        
        subgraph Multi-Agent Council (LangGraph / Gemini)
            SCADAAgent[SCADA Agent]
            PermitAgent[Permit Audit Agent]
            VisionAgent[CCTV Vision Agent]
            RegAgent[Regulatory Auditor Agent]
            Coord[Safety Coordinator]
            
            SCADAAgent <--> Coord
            PermitAgent <--> Coord
            VisionAgent <--> Coord
            RegAgent <--> Coord
        end
        
        StreamProcessor -->|Telemetry Tick| Coord
        SQLite <--> Coord
    end

    subgraph Control Room Cockpit (React + Vite)
        WSClient[WebSocket Real-time Client] <-->|Bidirectional WS| StreamProcessor
        WebUI[Dashboard: 2D Map, Alarms List, Telemetry Table, Dialogue Timeline, CCTV Console] <--> WSClient
        WebUI <-->|REST Requests| REST[API Router]
        REST <--> Ingest
    end
```

### 2. The Multi-Agent Safety Council
SafeOps AI runs four specialized agents to analyze hazards:
1. **SCADA Agent:** Focuses on process safety. Monitors temperature, pressures, and gas concentrations. Computes a localized physical hazard score and outputs SCADA directives (e.g., isolating gas lines).
2. **Permit Audit Agent:** Focuses on administrative safety compliance. Scans active Permits-to-Work (PTW) for location overlaps, SimOps conflicts (welding near confined entry), and operations near process warnings.
3. **CCTV Vision Agent:** Focuses on physical field compliance. Analyzes video logs for PPE violations (missing helmets/vests) and detects unauthorized entries into high-hazard confined space tanks.
4. **Safety Coordinator (Consensus Engine):** Synthesizes risk parameters into a final **Compound Risk Score (0-100)** using a weighted maximum algorithm: $CompoundRisk = \max(MaxAgentRisk, WeightedAverageRisk)$.
   * **The AI Debate:** When anomalies occur, the Coordinator initiates the Safety Council debate (using Gemini 1.5 Flash/Pro, or falling back on local structured templates if API keys are offline). SCADA, Permit, Vision, and Regulatory agents debate the threat, cite Indian Factories Act 1948 or OISD codes, and write a unified mitigation checklist.

---

## 📡 API Documentation

FastAPI automatically hosts the interactive API Swagger UI at `http://localhost:8000/docs`. Below is the REST & WebSocket specification:

### 1. WebSocket Endpoint
* **Path:** `/ws/telemetry`
* **Protocol:** Bidirectional WebSocket
* **Message Types (Server -> Client):**
  * `TELEMETRY_UPDATE`: Pushes live sensor values, worker locations, and permit registries.
  * `SAFETY_EVALUATION`: Pushes the Safety Council debate dialogue, compound risk score, active alerts, and citations.
  * `CCTV_EVENT`: Pushes live visual PPE alerts and movements.

### 2. REST API Routes
* **`GET /api/state`**
  * *Description:* Returns the current plant state (all sensors, workers, permits, active alerts).
  * *Response:* `{"sensors": [...], "workers": [...], "permits": [...], "alerts": [...]}`
* **`POST /api/permits/create`**
  * *Description:* Issues a new Digital Permit-to-Work.
  * *Payload:* `{"id": "PTW-ID", "type": "HOT_WORK | CONFINED_SPACE", "location": "Sector X", "issued_to": "Team A", ...}`
* **`POST /api/alerts/{alert_id}/acknowledge`**
  * *Description:* Marks an active alarm as acknowledged.
  * *Response:* Updated Alert model.
* **`GET /api/alerts/history`**
  * *Description:* Retrieves all generated alerts sorted by timestamp.
* **`GET /api/alerts/{alert_id}/report`**
  * *Description:* Fetches the statutory Form-22 preliminary accident report for the alert.
  * *Response:* IncidentReport model.
* **`POST /api/simulator/trigger`**
  * *Description:* Switches the active simulation scenario.
  * *Payload:* `{"scenario_id": "NORMAL | GAS_LEAK | HOT_WORK_CONFLICT | UNAUTHORIZED_WORKER | COMBINED_COMPOUND_RISK"}`

---

## 🚀 Sandbox Demo Guide & Scenarios

Use the simulator control buttons at the top of the dashboard to trigger these four demo scenarios:

| Scenario | Active Telemetry | Agent Reasoning Highlights | Risk Score | Expected UI Action |
|:---|:---|:---|:---:|:---|
| **Normal Ops** | Sensors fluctuate in safe ranges. Personnel move. | All parameters within safe limits. | **5%** | Status: "SYSTEM SECURE" (Green). |
| **Gas Leak** | CO gas sensor in Sector 1 drifts up to `45.0` ppm. | SCADA warns of CO gas. Permit Agent confirms Permit #001 is EXPIRED (no hot work conflict). Vision confirms Sector 1 is empty. | **55%** | Status: "WARNING DRIFT" (Orange). Sector 1 pulses orange. |
| **Hot Work Conflict** | CO gas sensor in Sector 1 drifts to `22.5` ppm. | Permit Agent flags that Hot Work Permit (welding) is active in Sector 1. Coordinator recommends temporary welding suspension. | **65%** | Status: "WARNING DRIFT" (Orange). Alarm card appears. |
| **Unauthorized Worker** | Rajesh Kumar enters Sector 2 confined space. | CCTV Vision Agent flags Rajesh has no active permit. SCADA warns of rapid toxic gas risks in storage tanks. | **75%** | Status: "HAZARD THREAT" (Red). Sector 2 pulses red. |
| **Compound Risk (Critical)** | CO gas spikes to `120` ppm in Sector 1. Amit Sharma welding in Sector 1. | SCADA flags critical gas. Permit Agent notes active welding. Regulatory Agent cites OISD-137. Coordinator triggers sirens. | **95%** | Status: "HAZARD THREAT" (Red/Pulse). Permit is **REVOKED**. Form-22 report generated. |

---

## 🎤 5-Minute Hackathon Presentation Flow

* **Minute 1: The Hook & The Problem**
  * *"Heavy industry pays a devastating human cost. Alarms exist, but they are siloed. When gas leaks happen during welding, no single sensor flags it until it's too late. That is the Compound Risk gap."*
* **Minute 2: The Solution (SafeOps AI)**
  * *"SafeOps AI is a real-time control room cockpit that unifies SCADA, Permits, and CCTV streams. We run a Multi-Agent Safety Council where agents representing process, permit compliance, and vision analytics negotiate safety in real-time."*
* **Minute 3: Live Demo (Scenarios)**
  * Switch to **Gas Leak**. Show that the sector turns orange, but the risk stays at 55% because no workers are present and permits are expired.
  * Switch to **Compound Risk**. The gas spikes, welding is active, and Amit is present. Risk spikes to 95%, sirens flash, and the permit is **REVOKED** automatically in the database.
* **Minute 4: Incident Report & RAG Audits**
  * Open the **Statutory Preliminary Report**. Show that SafeOps AI auto-generated a Form-22 accident report, complete with timeline and OISD/Factories Act violations, ready to print.
  * Click the **Reasoning Timeline** tab in the Safety panel to show the step-by-step risk trace of each agent.
* **Minute 5: Architecture & Business Value**
  * Wrap up with system architecture, SQLite state management, and the SaaS evolution roadmap (Neo4j, Kafka stream).

---

## 💻 Local & Docker Deployment Instructions

### 1. Running Locally (Manual Setup)

#### Prerequisites:
* Python 3.10+
* Node.js v18+

#### 1. Backend:
```bash
cd backend
# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --port 8000 --host 0.0.0.0 --reload
```
* Backend API: `http://localhost:8000`
* WebSocket Endpoint: `ws://localhost:8000/ws/telemetry`

#### 2. Frontend:
```bash
cd frontend
# Install dependencies
npm install

# Start Vite client
npm run dev
```
* Control Room UI: `http://localhost:5173`

---

### 2. Running via Docker Compose (SaaS Production Target)

If Docker is installed on your production target environment, simply run:
```bash
docker-compose up --build
```
This boots up the FastAPI container and React client container concurrently with shared volumes.
