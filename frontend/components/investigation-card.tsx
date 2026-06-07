"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Clock, Server, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";
import { Investigation } from "@/lib/api";

function timeSince(iso: string) {
  // Ensure UTC is parsed correctly — append Z if no timezone offset present
  const normalized = /[Z+\-]\d*$/.test(iso) ? iso : iso + "Z";
  const secs = Math.floor((Date.now() - new Date(normalized).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

function duration(inv: Investigation) {
  if (!inv.completed_at) return null;
  const normalize = (s: string) => /[Z+\-]\d*$/.test(s) ? s : s + "Z";
  return `${Math.round((new Date(normalize(inv.completed_at)).getTime() - new Date(normalize(inv.started_at)).getTime()) / 1000)}s`;
}

function SeverityBar({ severity }: { severity: string }) {
  const s = severity.toLowerCase();
  const color =
    s === "critical" ? "bg-red-500" :
    s === "high" ? "bg-orange-400" :
    s === "medium" ? "bg-yellow-400" : "bg-zinc-500";
  return <span className={`w-1 self-stretch rounded-full flex-shrink-0 ${color}`} />;
}

function StatusBadge({ status }: { status: string }) {
  if (status === "running")
    return (
      <Badge className="bg-primary/15 text-primary border-primary/20 gap-1 animate-pulse">
        <Loader2 className="w-3 h-3 animate-spin" /> Investigating
      </Badge>
    );
  if (status === "completed")
    return (
      <Badge className="bg-primary/15 text-primary border-primary/20 gap-1">
        <CheckCircle className="w-3 h-3" /> Resolved
      </Badge>
    );
  return (
    <Badge className="bg-destructive/15 text-destructive border-destructive/20 gap-1">
      <AlertTriangle className="w-3 h-3" /> Failed
    </Badge>
  );
}

export function InvestigationCard({ inv }: { inv: Investigation }) {
  const conf = Math.round((inv.confidence ?? 0) * 100);
  const dur = duration(inv);

  return (
    <Card className="bg-card/60 border-border/50 hover:border-border transition-colors overflow-hidden">
      <CardContent className="p-0">
        <div className="flex gap-0">
          <SeverityBar severity={inv.severity} />

          <div className="flex-1 p-5 space-y-4 min-w-0">
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="font-semibold text-sm text-foreground leading-snug truncate">
                  {inv.alert_name}
                </p>
                <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                  <span className="font-mono">{inv.id}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {timeSince(inv.started_at)}
                  </span>
                  {dur && <span>{dur}</span>}
                </div>
              </div>
              <StatusBadge status={inv.status} />
            </div>

            {/* Root cause */}
            {inv.root_cause ? (
              <div className="text-xs text-muted-foreground bg-muted/30 rounded-md px-3 py-2 leading-relaxed border border-border/30">
                <span className="text-foreground/50 font-medium uppercase tracking-wide text-[10px]">Root Cause · </span>
                {inv.root_cause}
              </div>
            ) : inv.status === "running" ? (
              <div className="text-xs text-muted-foreground bg-muted/20 rounded-md px-3 py-2 border border-border/20 flex items-center gap-2">
                <Loader2 className="w-3 h-3 animate-spin text-primary flex-shrink-0" />
                Agent is querying Splunk…
              </div>
            ) : null}

            {/* Confidence + first seen */}
            {(conf > 0 || inv.first_seen) && (
              <div className="flex items-center gap-6">
                {conf > 0 && (
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Confidence</span>
                      <span className="text-xs font-semibold text-primary">{conf}%</span>
                    </div>
                    <Progress value={conf} className="h-1" />
                  </div>
                )}
                {inv.first_seen && (
                  <div className="flex-shrink-0">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1">First Seen</p>
                    <p className="text-xs font-mono text-foreground">{inv.first_seen}</p>
                  </div>
                )}
              </div>
            )}

            {/* Affected hosts */}
            {inv.affected_hosts?.length > 0 && (
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1.5 flex items-center gap-1">
                  <Server className="w-3 h-3" /> {inv.affected_hosts.length} host{inv.affected_hosts.length > 1 ? "s" : ""}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {inv.affected_hosts.map((h) => (
                    <span
                      key={h}
                      className="font-mono text-[11px] bg-secondary text-muted-foreground border border-border/60 rounded px-2 py-0.5"
                    >
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendation */}
            {inv.recommendation && (
              <div className="flex items-start gap-2 text-xs text-primary bg-primary/5 border border-primary/15 rounded-md px-3 py-2 leading-relaxed">
                <CheckCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                {inv.recommendation}
              </div>
            )}

            {/* Error */}
            {inv.error && (
              <div className="text-xs text-red-400 bg-red-500/5 border border-red-500/15 rounded-md px-3 py-2">
                {inv.error}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
