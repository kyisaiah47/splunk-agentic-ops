"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { FlowLogo } from "@/components/flow-logo";
import { InvestigationCard } from "@/components/investigation-card";
import { fetchInvestigations, triggerAlert, type Investigation, type AlertType } from "@/lib/api";
import { Zap, Activity, CheckCircle2, TrendingUp, Circle } from "lucide-react";

const ALERT_OPTIONS: { key: AlertType; title: string; desc: string; severity: "critical" | "high" }[] = [
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

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      try {
        const data = await fetchInvestigations();
        setInvestigations(data);
        const hasRunning = data.some((i) => i.status === "running");
        timer = setTimeout(tick, hasRunning ? 2000 : 5000);
      } catch {
        timer = setTimeout(tick, 5000);
      }
    };
    tick();
    return () => clearTimeout(timer);
  }, []);

  async function handleTrigger(key: AlertType) {
    setTriggering(key);
    try {
      await triggerAlert(key);
      setDialogOpen(false);
      const data = await fetchInvestigations();
      setInvestigations(data);
    } finally {
      setTriggering(null);
    }
  }

  const running = investigations.filter((i) => i.status === "running");
  const completed = investigations.filter((i) => i.status === "completed");
  const avgConf =
    completed.length > 0
      ? Math.round((completed.reduce((s, i) => s + (i.confidence ?? 0), 0) / completed.length) * 100)
      : null;
  const isLive = running.length > 0;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* ── Hero / Command Center ─────────────────────────────── */}
      <div className="relative overflow-hidden border-b border-border/40"
        style={{
          background: "radial-gradient(ellipse 80% 60% at 50% -10%, oklch(0.5827 0.2187 36.98 / 12%) 0%, transparent 70%), oklch(0.1409 0.0059 285.64)",
        }}
      >
        {/* dot grid */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: "radial-gradient(circle, oklch(1 0 0 / 5%) 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />

        <div className="relative max-w-6xl mx-auto px-8 pt-8 pb-10">
          {/* Top bar */}
          <div className="flex items-center justify-between mb-10">
            <div className="flex items-center gap-3">
              <FlowLogo className="w-9 h-9 text-foreground" />
              <div>
                <h1 className="text-base font-semibold leading-none tracking-tight">Splunk Agentic Ops</h1>
                <p className="text-xs text-muted-foreground mt-0.5">Autonomous Incident Investigator</p>
              </div>
            </div>
            <Button size="sm" onClick={() => setDialogOpen(true)} className="gap-2">
              <Zap className="w-3.5 h-3.5" />
              Trigger Alert
            </Button>
          </div>

          {/* Status + Stats */}
          <div className="flex items-end justify-between gap-8">
            {/* Left: live status */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="relative flex h-2.5 w-2.5">
                  {isLive ? (
                    <>
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary" />
                    </>
                  ) : (
                    <Circle className="w-2.5 h-2.5 text-muted-foreground fill-muted-foreground" />
                  )}
                </span>
                <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
                  {isLive ? (
                    <span className="text-primary">{running.length} Investigation{running.length > 1 ? "s" : ""} Running</span>
                  ) : (
                    "System Standby"
                  )}
                </span>
              </div>
              <p className="text-5xl font-bold tracking-tight">
                {investigations.length > 0 ? investigations.length : "0"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">Total Investigations</p>
            </div>

            {/* Right: stat strip */}
            <div className="flex items-stretch gap-px rounded-xl overflow-hidden border border-border/40">
              {[
                {
                  icon: <Activity className="w-4 h-4" />,
                  label: "Running",
                  value: running.length,
                  highlight: running.length > 0,
                },
                {
                  icon: <CheckCircle2 className="w-4 h-4" />,
                  label: "Completed",
                  value: completed.length,
                  highlight: false,
                },
                {
                  icon: <TrendingUp className="w-4 h-4" />,
                  label: "Avg Confidence",
                  value: avgConf !== null ? `${avgConf}%` : "—",
                  highlight: false,
                },
              ].map((stat, i) => (
                <div
                  key={i}
                  className="bg-card/60 backdrop-blur-sm px-7 py-4 flex flex-col items-center gap-1 min-w-[120px]"
                >
                  <span className={stat.highlight ? "text-primary" : "text-muted-foreground"}>
                    {stat.icon}
                  </span>
                  <span className={`text-2xl font-bold tabular-nums ${stat.highlight ? "text-primary" : ""}`}>
                    {stat.value}
                  </span>
                  <span className="text-xs text-muted-foreground">{stat.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Investigations Grid ───────────────────────────────── */}
      <main className="max-w-6xl mx-auto px-8 py-8 w-full flex-1">
        <div className="flex items-center justify-between mb-5">
          <p className="text-xs text-muted-foreground uppercase tracking-widest font-medium">
            Investigations
            {investigations.length > 0 && (
              <span className="ml-2 text-foreground/40">({investigations.length})</span>
            )}
          </p>
          {running.length > 0 && (
            <span className="text-xs text-primary animate-pulse">
              Agent active — polling every 2s
            </span>
          )}
        </div>

        {investigations.length === 0 ? (
          <div className="mt-16 flex flex-col items-center gap-6 text-center">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center border border-border/40"
              style={{ background: "oklch(0.2108 0.0078 285.71)" }}
            >
              <Zap className="w-7 h-7 text-muted-foreground" />
            </div>
            <div>
              <p className="font-medium text-foreground">No investigations yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Trigger a demo alert or configure a Splunk webhook to get started
              </p>
            </div>
            <Button onClick={() => setDialogOpen(true)} className="gap-2 mt-1">
              <Zap className="w-3.5 h-3.5" />
              Trigger your first alert
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {investigations.map((inv) => (
              <InvestigationCard key={inv.id} inv={inv} />
            ))}
          </div>
        )}
      </main>

      {/* ── Trigger Dialog ────────────────────────────────────── */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Trigger a Demo Alert</DialogTitle>
          </DialogHeader>
          <Separator className="my-1 opacity-40" />
          <div className="space-y-2">
            {ALERT_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => handleTrigger(opt.key)}
                disabled={triggering !== null}
                className="w-full text-left rounded-lg border border-border/60 bg-muted/20 hover:bg-muted/50 hover:border-primary/40 transition-all p-4 disabled:opacity-50 disabled:cursor-not-allowed group"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      opt.severity === "critical"
                        ? "bg-red-500 shadow-[0_0_6px_#ef4444]"
                        : "bg-orange-400 shadow-[0_0_6px_#fb923c]"
                    }`}
                  />
                  <span className="text-sm font-medium">
                    {triggering === opt.key ? "Triggering…" : opt.title}
                  </span>
                  <span className="ml-auto text-xs text-muted-foreground uppercase tracking-wide border border-border/40 rounded px-1.5 py-0.5">
                    {opt.severity}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1.5 pl-5">{opt.desc}</p>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
