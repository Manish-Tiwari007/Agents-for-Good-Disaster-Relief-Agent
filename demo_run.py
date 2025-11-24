"""Direct orchestrator demo (bypasses HTTP) for recording video output.
Run: python demo_run.py
"""
from app import orchestrator
import json

result = orchestrator.act(goal="Flood relief allocation", supply={"water":4,"medical":2,"food":5}, max_loops=2, threshold=0.6)
print(json.dumps(result, indent=2))
