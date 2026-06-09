"""
Splunk Agentic Ops — FastAPI backend

Endpoints:
  POST /webhook/splunk     Splunk alert webhook → triggers investigation
  GET  /investigations     List all past investigations
  GET  /investigations/{id} Get one investigation
  GET  /health             Liveness check
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from agent.investigator import investigate_alert
from models import AlertWebhook, Investigation
from notifications.slack import post_investigation_report

load_dotenv()

# In-memory store (good enough for a hackathon demo)
investigations: Dict[str, Investigation] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Splunk Agentic Ops is running.")
    yield


app = FastAPI(
    title="Splunk Agentic Ops",
    description="AI-powered autonomous incident investigation using Splunk and Claude.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------

async def _run_investigation(alert: AlertWebhook, inv_id: str) -> None:
    inv = await investigate_alert(alert, inv_id=inv_id)
    investigations[inv.id] = inv
    await post_investigation_report(inv)
    status = "completed" if inv.status == "completed" else "FAILED"
    print(f"[{inv.id}] Investigation {status} — {inv.root_cause or inv.error}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/webhook/splunk", status_code=202)
async def splunk_webhook(alert: AlertWebhook, background_tasks: BackgroundTasks):
    """
    Splunk calls this URL when a saved-search alert fires.
    Configure in Splunk: Alert Actions → Webhook → URL = http://<host>:8000/webhook/splunk
    """
    # Placeholder investigation so callers get an immediate ID back
    from datetime import datetime
    import uuid
    inv_id = str(uuid.uuid4())[:8]
    placeholder = Investigation(
        id=inv_id,
        alert_name=alert.alert_name,
        severity=alert.severity,
    )
    investigations[inv_id] = placeholder
    background_tasks.add_task(_run_investigation, alert, inv_id)
    return {"status": "accepted", "investigation_id": inv_id}


@app.get("/investigations", response_model=list[Investigation])
async def list_investigations():
    return sorted(investigations.values(), key=lambda i: i.started_at, reverse=True)


@app.get("/investigations/{inv_id}", response_model=Investigation)
async def get_investigation(inv_id: str):
    inv = investigations.get(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@app.get("/")
async def dashboard():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "investigations": len(investigations)}


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)
