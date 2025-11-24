"""FastAPI service wrapping the disaster relief multi-agent orchestration.
Do NOT commit secrets. Set GOOGLE_API_KEY before starting if using Gemini.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
import time, uuid, os, logging
from collections import deque

# Optional Gemini (graceful fallback)
try:
    import google.generativeai as genai  # noqa: F401
except Exception:
    class StubGenAI:
        def configure(self, **kwargs):
            pass
    genai = StubGenAI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger("service")

# ------------------ Core Schemas ------------------
class Message:
    def __init__(self, sender: str, role: str, content: str, metadata: Dict[str, Any] | None = None):
        self.sender = sender
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.id = str(uuid.uuid4())
    def compact(self):
        return {"s": self.sender, "r": self.role, "c": self.content[:160], "t": round(self.timestamp,2)}

class A2ABus:
    def __init__(self):
        self.messages: List[Message] = []
    def publish(self, msg: Message):
        self.messages.append(msg)
    def recent(self, n:int=12):
        return self.messages[-n:]
    def summary(self):
        return "\n".join(f"[{m.role}] {m.sender}: {m.content[:100]}" for m in self.recent())

bus = A2ABus()

# ------------------ Memory ------------------
class SessionMemory:
    def __init__(self, max_messages:int=60):
        self.buffer = deque(maxlen=max_messages)
    def add(self, msg: Message):
        self.buffer.append(msg)
    def compact(self):
        subset = list(self.buffer)[-10:]
        return " | ".join(f"{m.role}:{m.content[:60]}" for m in subset)

session_memory = SessionMemory()

# ------------------ Tools ------------------
class SearchTool:
    name = "search"
    def run(self, query: str):
        # Simulated; replace with real search / API calls
        import random
        results = [
            {"title": "Site A", "need": "water", "severity": random.randint(1,10)},
            {"title": "Site B", "need": "medical", "severity": random.randint(1,10)},
            {"title": "Site C", "need": "food", "severity": random.randint(1,10)}
        ]
        return {"query": query, "results": results}

class ResourceAllocationTool:
    name = "allocator"
    def run(self, demands: List[Dict[str, Any]], supply: Dict[str,int]):
        allocation = []
        for d in demands:
            need = d['need']
            if supply.get(need,0) > 0:
                supply[need] -= 1
                allocation.append({"location": d['title'], "allocated": need})
        return {"allocation": allocation, "remaining": supply}

search_tool = SearchTool()
alloc_tool = ResourceAllocationTool()

# ------------------ Agents ------------------
class BaseAgent:
    def __init__(self, name:str, role:str):
        self.name = name
        self.role = role
    def send(self, content:str, metadata:Dict[str,Any]|None=None):
        msg = Message(self.name, self.role, content, metadata)
        bus.publish(msg)
        session_memory.add(msg)
        return msg

class PlannerAgent(BaseAgent):
    def act(self, goal:str):
        steps = ["retrieve", "allocate", "evaluate"]
        self.send(f"Plan created for goal '{goal}' -> {steps}")
        return steps

class RetrievalAgent(BaseAgent):
    def act(self, goal:str):
        data = search_tool.run(query=goal)
        self.send(f"Retrieved {len(data['results'])} items")
        return data

class ExecutionAgent(BaseAgent):
    def act(self, situational:Dict[str,Any], supply:Dict[str,int]):
        alloc = alloc_tool.run(demands=situational.get("results",[]), supply=supply)
        self.send(f"Allocated {len(alloc['allocation'])} resources")
        return alloc

class EvaluationAgent(BaseAgent):
    def act(self, allocation:Dict[str,Any]):
        total_alloc = len(allocation.get("allocation",[]))
        remaining = sum(allocation.get("remaining",{}).values())
        score = total_alloc / (total_alloc + remaining + 0.0001)
        result = {"effectiveness_score": round(score,2), "allocated": total_alloc, "remaining_supply": allocation.get("remaining",{})}
        self.send(f"Evaluation score={result['effectiveness_score']}")
        return result

class Orchestrator(BaseAgent):
    def __init__(self):
        super().__init__("orchestrator", "orchestrator")
        self.planner = PlannerAgent("planner","planner")
        self.retrieval = RetrievalAgent("retrieval","retrieval")
        self.execution = ExecutionAgent("execution","execution")
        self.evaluation = EvaluationAgent("evaluation","evaluation")

    def act(self, goal:str, supply:Dict[str,int], max_loops:int=2, threshold:float=0.7):
        self.send(f"Starting orchestration for goal='{goal}'")
        self.planner.act(goal)
        report = {}
        for loop in range(1, max_loops+1):
            self.send(f"Loop {loop} context={session_memory.compact()}")
            situ = self.retrieval.act(goal)
            alloc = self.execution.act(situ, supply.copy())
            eval_r = self.evaluation.act(alloc)
            report = {"loop": loop, "situational": situ, "allocation": alloc, "evaluation": eval_r}
            if eval_r['effectiveness_score'] >= threshold:
                self.send(f"Threshold reached loop={loop}")
                break
        self.send("Orchestration complete")
        report["conversation_summary"] = bus.summary()
        return report

orchestrator = Orchestrator()

# ------------------ API Models ------------------
class OrchestrateRequest(BaseModel):
    goal: str
    water: int = 3
    medical: int = 2
    food: int = 4

class OrchestrateResponse(BaseModel):
    loop: int
    evaluation: Dict[str, Any]
    allocation: Dict[str, Any]
    situational: Dict[str, Any]
    conversation_summary: str

app = FastAPI(title="Disaster Relief Multi-Agent Service", version="1.0.0")

@app.get('/')
def root():
    """Simple landing endpoint to avoid 404 when opening in browser.
    Shows basic info and available primary routes.
    """
    return {
        "service": app.title,
        "version": app.version,
        "endpoints": ["/health", "/orchestrate", "/docs", "/openapi.json"],
        "note": "Use /docs for interactive API or POST /orchestrate"
    }

@app.post('/orchestrate', response_model=OrchestrateResponse)
def orchestrate(req: OrchestrateRequest):
    supply = {"water": req.water, "medical": req.medical, "food": req.food}
    result = orchestrator.act(goal=req.goal, supply=supply)
    return OrchestrateResponse(**result)

@app.get('/health')
def health():
    return {"status": "ok", "agents": ["planner","retrieval","execution","evaluation","orchestrator"], "messages": len(bus.messages)}

# Run via: uvicorn app:app --host 0.0.0.0 --port 8000
