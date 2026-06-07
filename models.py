from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class AlertWebhook(BaseModel):
    alert_name: str
    search_name: str = ""
    search_query: str = ""
    trigger_time: str = ""
    severity: str = "medium"
    trigger_reason: Dict[str, Any] = {}
    results: Optional[Dict[str, Any]] = None
    owner: Optional[str] = None


class Evidence(BaseModel):
    tool: str
    query: Dict[str, Any]
    result_preview: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Investigation(BaseModel):
    id: str
    alert_name: str
    severity: str = "medium"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"
    root_cause: Optional[str] = None
    confidence: float = 0.0
    first_seen: Optional[str] = None
    affected_hosts: List[str] = []
    affected_services: List[str] = []
    recommendation: Optional[str] = None
    summary: Optional[str] = None
    evidence: List[Evidence] = []
    error: Optional[str] = None
