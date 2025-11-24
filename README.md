# Agents-for-Good-Disaster-Relief-Agent

Keywords: disaster-relief, gemini API, multi-agent, fastapi, streamlit

## Problem
Disaster response suffers from fragmented information, inefficient resource allocation, and delayed assistance. Manual coordination does not scale during high-impact events (floods, earthquakes, storms).

##  Solution
A multi-agent system orchestrating planning, retrieval of situational data, resource allocation, and iterative evaluation with memory and observability. Extensible tool layer enables future integration with real data sources (APIs, sensor feeds, MCP tooling).

##  Architecture Overview
Agents: Planner -> Retrieval -> Execution -> Evaluation under Orchestrator loop.
Tools: SearchTool (simulated), ResourceAllocationTool, MCP.
Memory: Session buffer with compaction heuristics (vector memory in notebook version).
Observability: Logging; OpenTelemetry-ready (not required for basic run).
Evaluation: Effectiveness score based on allocated vs remaining supply.

##  Features Demonstrated
- Multi-agent sequential + loop orchestration.
- Custom tools abstraction and registry.
- Session memory + context compaction.
- A2A style message bus for structured communication.
- Evaluation harness for metrics (in notebook).
- Deployment-ready FastAPI service (`app.py`).

## 5. Requirements
See `requirements.txt`. Heavy packages (sentence-transformers) can be removed if not needed.

##  Quick Minimal Startup
If you only need the API running for demo (no embeddings, no diagram generation):
```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install fastapi==0.115.0 uvicorn==0.30.0 pydantic>=2.12.4 httpx
uvicorn app:app --host 127.0.0.1 --port 8000
```
Test endpoints:
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health -Method GET
$body = @{goal='Flood relief allocation'; water=3; medical=2; food=4} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/orchestrate -Method POST -Body $body -ContentType 'application/json'
```
If `conda activate myenv` fails, prefer the above local venv instead of Conda to avoid path issues.

###  Streamlit Frontend
Add a simple UI for user interaction.
```powershell
streamlit run streamlit_app.py
```
Modes:
- HTTP API (requires backend running: `uvicorn app:app --host 127.0.0.1 --port 8000`)
- Direct Import (runs agents in-process; backend not required)

If activation scripts are blocked by execution policy, you can bypass venv activation:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```


##  Local Setup (Windows PowerShell)
```powershell
# Clone or open project directory
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# (Optional) Set Gemini key if you will integrate LLM
$env:GOOGLE_API_KEY = "YOUR_KEY_HERE"

# Run API
# Run API (bind on all interfaces)
# NOTE: Use http://127.0.0.1:8000 or http://localhost:8000 in your browser.
# 0.0.0.0 is a bind address, not a routable hostname, so browsers may reject it.
uvicorn app:app --host 0.0.0.0 --port 8000

# If using the conda environment directly (without activating in this shell):
# E:/Anaconda/Scripts/conda.exe run -p C:\Users\WCC\.conda\envs\myenv python -m uvicorn app:app --host 0.0.0.0 --port 8000
```^

##  Test Endpoints
Health check:
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health -Method GET
```
Orchestrate example:
```powershell
$body = @{goal="Flood relief allocation"; water=4; medical=2; food=5} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/orchestrate -Method POST -Body $body -ContentType "application/json"
```


## Deployment (Cloud Run Example)
```bash
docker build -t gcr.io/PROJECT_ID/disaster-agents:latest .
docker push gcr.io/PROJECT_ID/disaster-agents:latest
gcloud run deploy disaster-agents \
  --image gcr.io/PROJECT_ID/disaster-agents:latest \
  --platform managed --region REGION --allow-unauthenticated
```
##  Safety & Keys
No secrets committed. 

##  Next Steps
- Integrate real-time feeds (geospatial, social signals).
- Advanced prioritization using severity + vulnerability indices.
- Parallel retrieval + streaming evaluation.
- Full OpenTelemetry export + dashboards.

  
##  Troubleshooting (Local Run)


### Quick Verification Commands (PowerShell)
```powershell
# Check server reachable
Invoke-RestMethod -Uri http://127.0.0.1:8000/health -Method GET

# If failing, confirm process
Get-Process -Name python | Select-Object Id, ProcessName

# List listening ports (requires admin for full info)
netstat -ano | findstr :8000
```

### Alternative Direct Run Without HTTP
```powershell
python demo_run.py
```
Generates JSON output you can show in the demo if HTTP testing is blocked.




