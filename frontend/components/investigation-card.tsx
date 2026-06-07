"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ChevronDown, ChevronUp, Clock, Server, Zap, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";
import { Investigation } from "@/lib/api";

function timeSince(iso: string) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  return `${Math.floor(secs / 3600)}h ago`;
}

function duration(inv: Investigation) {
  if (!inv.completed_at) return null;
  const ms = new Date(inv.completed_at).getTime() - new Date(inv.started_at).getTime();
  return `${Math.round(ms / 1000)}s`;
}

function SeverityIndicator({ severity }: { severity: string }) {
  const s = severity.toLowerCase();
  if (s === "critical") return <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_6px_#ef4444] flex-shrink-0" />;
  if (s === "high") return <span className="w-2 h-2 rounded-full bg-orange-400 shadow-[0_0_6px_#fb923c] flex-shrink-0" />;
  if (s === "medium") return <span className="w-2 h-2 rounded-full bg-yellow-400 flex-shrink-0" />;
  return <span className="w-2 h-2 rounded-full bg-zinc-500 flex-shrink-0" />;
}

function StatusBadge({ status }: { status: string }) {
  if (status === "running")
    return <Badge className="bg-blue-500/15 text-blue-400 border-blue-500/20 animate-pulse gap-1"><Loader2 className="w-3 h-3 animate-spin" />Running</Badge>;
  if (status === "completed")
    return <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/20 gap-1"><CheckCircle className="w-3 h-3" />Completed</Badge>;
  return <Badge className="bg-red-500/15 text-red-400 border-red-500/20 gap-1"><AlertTriangle className="w-3 h-3" />Failed</Badge>;
}

export function InvestigationCard({ inv }: { inv: Investigation }) {
  const [expanded, setExpanded] = useState(false);
  const dur = duration(inv);
  const conf = Math.round((inv.confidence ?? 0) * 100);

  return (
    <Card
      className="cursor-pointer transition-all border-border/50 hover:border-border bg-card/60 backdrop-blur-sm"
      onClick={() => setExpanded((v) => !v)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <SeverityIndicator severity={inv.severity} />
          <span className="font-medium text-foreground flex-1 text-sm">{inv.alert_name}</span>
          <StatusBadge status={inv.status} />
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          )}
        </div>
        <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1 pl-5">
          <span className="font-mono">{inv.id}</span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timeSince(inv.started_at)}
          </span>
          {dur && <span>{dur} investigation</span>}
          {conf > 0 && <span className="text-primary font-medium">{conf}% confidence</span>}
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 space-y-4" onClick={(e) => e.stopPropagation()}>
          <Separator className="opacity-50" />

          {inv.root_cause && (
            <div className="rounded-lg bg-muted/40 border border-border/50 p-3 text-sm">
              <span className="text-muted-foreground text-xs uppercase tracking-wide font-medium">Root Cause</span>
              <p className="mt-1 text-foreground">{inv.root_cause}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Confidence</p>
              <div className="flex items-center gap-2">
                <Progress value={conf} className="h-1.5 flex-1" />
                <span className="text-xs font-medium text-primary w-8 text-right">{conf}%</span>
              </div>
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">First Seen</p>
              <p className="text-foreground font-mono text-xs">{inv.first_seen ?? "—"}</p>
            </div>

            {(inv.affected_hosts?.length > 0) && (
              <div className="col-span-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                  <Server className="w-3 h-3" /> Affected Hosts
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {inv.affected_hosts.map((h) => (
                    <span key={h} className="font-mono text-xs bg-blue-500/10 text-blue-300 border border-blue-500/20 rounded px-2 py-0.5">
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {inv.summary && (
            <div className="rounded-lg bg-muted/30 border border-border/40 p-3 text-sm text-muted-foreground leading-relaxed">
              {inv.summary}
            </div>
          )}

          {inv.recommendation && (
            <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-3 text-sm text-emerald-300 leading-relaxed flex gap-2">
              <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              {inv.recommendation}
            </div>
          )}

          {inv.evidence?.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                <Zap className="w-3 h-3" /> Evidence ({inv.evidence.length} queries)
              </p>
              <div className="space-y-1.5">
                {inv.evidence.slice(0, 6).map((e, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="bg-muted rounded px-1.5 py-0.5 font-mono flex-shrink-0 text-foreground/60">
                      {e.tool}
                    </span>
                    <span className="truncate">{Object.values(e.query ?? {})[0] ?? ""}…</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {inv.error && (
            <div className="rounded-lg bg-red-500/5 border border-red-500/20 p-3 text-sm text-red-400">
              {inv.error}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
