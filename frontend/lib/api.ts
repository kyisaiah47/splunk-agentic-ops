const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:9000";
const HEADERS: Record<string, string> = {
  "bypass-tunnel-reminder": "true",
  "ngrok-skip-browser-warning": "true",
};

export interface Evidence {
  tool: string;
  query: Record<string, string>;
  result_preview: string;
}

export interface Investigation {
  id: string;
  alert_name: string;
  severity: string;
  status: "running" | "completed" | "failed";
  started_at: string;
  completed_at: string | null;
  root_cause: string | null;
  confidence: number;
  first_seen: string | null;
  affected_hosts: string[];
  affected_services: string[];
  summary: string | null;
  recommendation: string | null;
  evidence: Evidence[];
  error: string | null;
}

export async function fetchInvestigations(): Promise<Investigation[]> {
  const res = await fetch(`${API}/investigations`, { cache: "no-store", headers: HEADERS });
  if (!res.ok) throw new Error("Failed to fetch");
  return res.json();
}

export type AlertType = "5xx_spike" | "latency" | "db_connections";

const PAYLOADS: Record<AlertType, object> = {
  "5xx_spike": {
    alert_name: "High 5xx Error Rate — Web Tier",
    search_query: "index=web_logs status>=500 | stats count by host",
    severity: "high",
    trigger_time: new Date().toISOString(),
    trigger_reason: { type: "threshold", value: "847 errors", condition: "> 50 per host in 15 min" },
  },
  latency: {
    alert_name: "P99 Latency Exceeds SLO (>2s)",
    search_query: 'index=web_logs | rex field=_raw "(?P<ms>\\d+)ms$" | eventstats p99(ms) as p99 | where p99>2000',
    severity: "high",
    trigger_time: new Date().toISOString(),
    trigger_reason: { type: "p99 latency", value: "4823ms", condition: "> 2000ms" },
  },
  db_connections: {
    alert_name: "Database Connection Pool Exhausted",
    search_query: 'index=app_logs "connection pool exhausted" | stats count by host',
    severity: "critical",
    trigger_time: new Date().toISOString(),
    trigger_reason: { type: "threshold", value: "245 events", condition: "> 10" },
  },
};

export async function triggerAlert(type: AlertType): Promise<{ investigation_id: string }> {
  const res = await fetch(`${API}/webhook/splunk`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...HEADERS },
    body: JSON.stringify({ ...PAYLOADS[type], trigger_time: new Date().toISOString() }),
  });
  if (!res.ok) throw new Error("Failed to trigger alert");
  return res.json();
}
