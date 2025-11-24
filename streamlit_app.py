"""Streamlit frontend for Disaster Relief Multi-Agent Coordination System.
Run: streamlit run streamlit_app.py

Features:
- Input goal and supply quantities
- Choose mode: HTTP API call or direct in-process orchestration
- Display evaluation score, allocation table, situational results
- Show conversation summary and architecture diagram if available
"""
import os
import json
from pathlib import Path
import time
import streamlit as st

# Prefer requests for simplicity
try:
    import requests  # type: ignore
except Exception:  # fallback minimal HTTP via httpx if installed
    import httpx as requests  # type: ignore

BACKEND_URL_DEFAULT = "http://127.0.0.1:8000"

st.set_page_config(page_title="Disaster Relief Orchestrator", page_icon="🛰️", layout="wide")
st.title("🛰️ Disaster Relief Multi-Agent Orchestrator")
st.caption("Interactive frontend: plan → retrieve → execute → evaluate")

mode = st.radio("Execution Mode", ["HTTP API", "Direct Import"], help="HTTP calls the running FastAPI service; Direct Import runs agents inside this process.")
backend_url = st.text_input("Backend URL", BACKEND_URL_DEFAULT, disabled=(mode != "HTTP API"))

col_goal, col_water, col_med, col_food = st.columns([3,1,1,1])
with col_goal:
    goal = st.text_input("Goal / Scenario", value="Flood relief allocation")
with col_water:
    water = st.number_input("Water", min_value=0, value=3)
with col_med:
    medical = st.number_input("Medical", min_value=0, value=2)
with col_food:
    food = st.number_input("Food", min_value=0, value=4)

advanced = st.expander("Advanced Settings")
with advanced:
    max_loops = st.slider("Max Loops", 1, 5, 2)
    threshold = st.slider("Effectiveness Threshold", 0.3, 0.99, 0.7)
    show_conversation = st.checkbox("Show conversation summary", value=True)

run_btn = st.button("Run Orchestration", type="primary")

result = None
latency_ms = None
error = None

if run_btn:
    start = time.time()
    try:
        if mode == "HTTP API":
            payload = {"goal": goal, "water": water, "medical": medical, "food": food}
            resp = requests.post(f"{backend_url}/orchestrate", json=payload, timeout=60)
            if resp.status_code != 200:
                error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            else:
                result = resp.json()
        else:  # Direct Import
            from app import orchestrator  # local import
            supply = {"water": water, "medical": medical, "food": food}
            result = orchestrator.act(goal=goal, supply=supply, max_loops=max_loops, threshold=threshold)
        latency_ms = round((time.time() - start) * 1000, 1)
    except Exception as e:  # noqa: BLE001
        error = str(e)

# Layout for results
if error:
    st.error(f"❌ Error: {error}")
elif result:
    st.success(f"✅ Completed loop {result.get('loop')} in {latency_ms} ms")
    eval_r = result.get("evaluation", {})
    allocation = result.get("allocation", {})
    situ = result.get("situational", {})

    # Top KPIs
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Effectiveness Score", str(eval_r.get("effectiveness_score")))
    kpi2.metric("Allocated Count", str(eval_r.get("allocated")))
    remaining_supply = eval_r.get("remaining_supply", {})
    kpi3.metric("Remaining Supply", ", ".join(f"{k}:{v}" for k, v in remaining_supply.items()) or "None")

    st.subheader("Resource Allocation")
    alloc_table = allocation.get("allocation", [])
    if alloc_table:
        st.table(alloc_table)
    else:
        st.write("No resources allocated.")

    st.subheader("Situational Retrieval Results")
    st.json(situ)

    if show_conversation:
        st.subheader("Conversation Summary")
        st.text(result.get("conversation_summary", "(empty)"))

# Architecture diagram if exists
diagram_path = Path("architecture.png")
if diagram_path.exists():
    st.divider()
    st.caption("Architecture Diagram")
    st.image(str(diagram_path), use_column_width=True)
else:
    st.caption("(Generate architecture.png via architecture_diagram.py to display diagram)")

st.divider()
st.markdown("**Run Tips**")
st.markdown("- Start backend first for HTTP mode: `uvicorn app:app --host 127.0.0.1 --port 8000`\n- Use Direct Import if you cannot start the server or want quicker iteration.\n- The effectiveness score stops loops early when reaching threshold.")

st.markdown("**Troubleshooting**")
st.markdown("If HTTP mode fails: verify server log, check port, ensure packages installed. For SSL or proxy issues, try Direct Import mode.")

