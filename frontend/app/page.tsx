"use client";

import { useEffect, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { FlowLogo } from "@/components/flow-logo";
import { InvestigationCard } from "@/components/investigation-card";
import { fetchInvestigations, triggerAlert, type Investigation, type AlertType } from "@/lib/api";
import { Activity, Search, Zap } from "lucide-react";

const ALERT_OPTIONS: { key: AlertType; title: string; desc: string; severity: string }[] = [
  {
    key: "5xx_spike",
    title: "High 5xx Error Rate",
    desc: "500/503 spike on web-03 and web-07 — bad deployment scenario",
    severity: "high",
  },
  {
    key: "latency",
    title: "P99 Latency SLO Breach",
    desc: "Response times exceed 2s across all hosts",
    severity: "high",
  },
  {
    key: "db_connections",
    title: "Database Connection Pool Exhausted",
    desc: "Connection pool full — cascading failure risk",
    severity: "critical",
  },
];

export default function Dashboard() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [triggering, setTriggering] = useState<AlertType | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchInvestigations();
      setInvestigations(data);
    } catch {}
  }, []);

  useEffect(() => {
    load();
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      await load();
      const hasRunning = investigations.some((i) => i.status === "running");
      timer = setTimeout(tick, hasRunning ? 2000 : 5000);
    };
    timer = setTimeout(tick, 2000);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  async function handleTrigger(key: AlertType) {
    setTriggering(key);
    try {
      await triggerAlert(key);
      setDialogOpen(false);
      await load();
    } finally {
      setTriggering(null);
    }
  }

  const completed = investigations.filter((i) => i.status === "completed");
  const avgConf =
    completed.length > 0
      ? Math.round((completed.reduce((s, i) => s + (i.confidence ?? 0), 0) / completed.length) * 100)
      : null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/40 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FlowLogo className="w-8 h-8" />
            <div>
              <h1 className="text-sm font-semibold text-foreground leading-none">Splunk Agentic Ops</h1>
              <p className="text-xs text-muted-foreground mt-0.5">Autonomous Incident Investigator</p>
            </div>
          </div>
          <Button size="sm" onClick={() => setDialogOpen(true)} className="gap-2">
            <Zap className="w-3.5 h-3.5" />
            Trigger Alert
          </Button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 w-full flex-1 space-y-8">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="bg-card/60 border-border/50">
            <CardContent className="pt-5 pb-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Total</p>
                  <p className="text-3xl font-bold mt-1">{investigations.length || "—"}</p>
                </div>
                <Activity className="w-5 h-5 text-muted-foreground mt-1" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/60 border-border/50">
            <CardContent className="pt-5 pb-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Completed</p>
                  <p className="text-3xl font-bold mt-1">{completed.length || "—"}</p>
                </div>
                <Search className="w-5 h-5 text-muted-foreground mt-1" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/60 border-border/50">
            <CardContent className="pt-5 pb-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Avg Confidence</p>
                  <p className="text-3xl font-bold mt-1 text-primary">
                    {avgConf !== null ? `${avgConf}%` : "—"}
                  </p>
                </div>
                <Zap className="w-5 h-5 text-muted-foreground mt-1" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Investigation list */}
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide font-medium">Investigations</p>
          {investigations.length === 0 ? (
            <div className="text-center py-20 text-muted-foreground">
              <Search className="w-10 h-10 mx-auto mb-4 opacity-30" />
              <p className="text-sm">No investigations yet — trigger an alert to get started</p>
            </div>
          ) : (
            investigations.map((inv) => <InvestigationCard key={inv.id} inv={inv} />)
          )}
        </div>
      </main>

      {/* Trigger dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Trigger a Demo Alert</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 mt-2">
            {ALERT_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => handleTrigger(opt.key)}
                disabled={triggering !== null}
                className="w-full text-left rounded-lg border border-border/60 bg-muted/30 hover:bg-muted/60 hover:border-primary/30 transition-all p-4 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    opt.severity === "critical"
                      ? "bg-red-500 shadow-[0_0_6px_#ef4444]"
                      : "bg-orange-400 shadow-[0_0_6px_#fb923c]"
                  }`} />
                  <span className="text-sm font-medium text-foreground">
                    {triggering === opt.key ? "Triggering…" : opt.title}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1 pl-4">{opt.desc}</p>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
