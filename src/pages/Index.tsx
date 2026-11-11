import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Activity, AlertTriangle, ArrowLeft, CheckCircle2, Clock3, DollarSign, LoaderCircle, Play, Plus, Radio, Search, Shield, WifiOff, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { Breaker, createRun, getRun, getRunEvents, listBreakers, listRuns, listTools, metricsSummary, RunDetail as RunDetailData, RunEvent, RunSummary, ToolSpec } from "@/lib/api";

const examples = ["What is the capital of France?", "Calculate 2 + 3 * 4", "How to make a bomb"];
const runStages = [
  { event: "intake_guard", label: "Intake" },
  { event: "planner", label: "Planner" },
  { event: "approval_gate", label: "Approval" },
  { event: "worker", label: "Worker" },
  { event: "verifier", label: "Verifier" },
  { event: "finalize", label: "Finalize" },
];

function statusTone(status: string) {
  if (status === "completed" || status === "closed") return "border-emerald-400/30 bg-emerald-400/10 text-emerald-300";
  if (status === "blocked" || status === "failed" || status === "open") return "border-rose-400/30 bg-rose-400/10 text-rose-300";
  if (status === "running" || status === "half_open") return "border-cyan-400/30 bg-cyan-400/10 text-cyan-200";
  return "border-amber-300/30 bg-amber-300/10 text-amber-200";
}

function LoadingCards() {
  return <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }, (_, index) => <Skeleton key={index} className="h-32 rounded-2xl bg-white/[0.06]" />)}</div>;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function RunDetailPanel({ runId, onBack }: { runId: string; onBack: () => void }) {
  const [detail, setDetail] = useState<RunDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [socketOnline, setSocketOnline] = useState(false);
  const lastSeq = useRef(0);

  useEffect(() => {
    let alive = true;
    const refresh = async () => {
      try {
        const result = await getRun(runId);
        if (alive) setDetail(result);
      } catch {
        if (alive) setDetail(null);
      } finally {
        if (alive) setLoading(false);
      }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [runId]);

  useEffect(() => {
    lastSeq.current = 0;
    setEvents([]);
    setSocketOnline(false);
    let socket: WebSocket | null = null;
    try {
      socket = new WebSocket(`ws://127.0.0.1:8000/api/v1/ws/runs/${encodeURIComponent(runId)}?last_seq=0`);
      socket.onopen = () => setSocketOnline(true);
      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(String(message.data)) as RunEvent;
          if (event.type !== "heartbeat") appendEvent(event);
        } catch {
          setSocketOnline(false);
        }
      };
      socket.onerror = () => setSocketOnline(false);
      socket.onclose = () => setSocketOnline(false);
    } catch {
      setSocketOnline(false);
    }
    return () => socket?.close();

    function appendEvent(event: RunEvent) {
      if (typeof event.seq !== "number" || event.seq <= lastSeq.current) return;
      lastSeq.current = event.seq;
      setEvents((current) => [...current, event]);
    }
  }, [runId]);

  useEffect(() => {
    if (socketOnline) return;
    let alive = true;
    const poll = async () => {
      try {
        const fresh = await getRunEvents(runId, lastSeq.current);
        if (!alive) return;
        for (const event of fresh) {
          if (event.seq > lastSeq.current) {
            lastSeq.current = event.seq;
            setEvents((current) => [...current, event]);
          }
        }
      } catch {
        // Run detail polling still provides the current state when event replay is unavailable.
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 1000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [runId, socketOnline]);

  const blocked = detail?.status === "blocked" || detail?.report?.verdict === "block";
  const completedStages = new Set(events.filter((event) => event.type === "node.completed").map((event) => event.node));
  const nextStage = runStages.find((stage) => !completedStages.has(stage.event))?.event;

  return (
    <section className="space-y-5">
      <Button variant="ghost" onClick={onBack} className="gap-2 px-0 text-slate-300 hover:text-white"><ArrowLeft className="h-4 w-4" /> Back to runs</Button>
      {loading ? <Skeleton className="h-64 rounded-2xl bg-white/[0.06]" /> : !detail ? <div className="rounded-xl border border-rose-400/20 bg-rose-400/5 p-5 text-rose-200">Could not load run details.</div> : <>
        <div className="grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
          <Card className="border-white/10 bg-slate-900/75 text-slate-100">
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div><p className="mb-2 font-mono text-xs text-slate-500">{detail.id}</p><CardTitle className="text-xl">{detail.task}</CardTitle></div>
              <Badge className={statusTone(detail.status)}>{detail.status}</Badge>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-3">
              <div><p className="text-xs uppercase tracking-wider text-slate-500">Intent</p><p className="mt-1">{detail.intent ?? "—"}</p></div>
              <div><p className="text-xs uppercase tracking-wider text-slate-500">Created</p><p className="mt-1 text-sm">{formatDate(detail.created_at)}</p></div>
              <div><p className="text-xs uppercase tracking-wider text-slate-500">Cost</p><p className="mt-1">${detail.budget.cost_usd.toFixed(4)}</p></div>
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-slate-900/75 text-slate-100">
            <CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-base">Live agent flow</CardTitle><span className="flex items-center gap-2 text-xs text-slate-400"><Radio className={`h-3.5 w-3.5 ${socketOnline ? "text-emerald-400" : "text-amber-300"}`} />{socketOnline ? "Live" : "Polling"}</span></CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-2">
                {blocked ? <>
                  {["Intake", "Refusal"].map((label, index) => <div key={label} className="flex items-center gap-2"><div className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-200"><span className="mr-2 text-rose-400">●</span>{label}</div>{index === 0 && <span className="text-slate-600">→</span>}</div>)}
                </> : runStages.map((stage, index) => {
                  const done = completedStages.has(stage.event);
                  const active = !done && nextStage === stage.event && !["completed", "failed", "blocked"].includes(detail.status);
                  return <div key={stage.event} className="flex items-center gap-2"><div className={`rounded-xl border px-3 py-2 text-sm transition ${done ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-200" : active ? "border-cyan-300/60 bg-cyan-300/10 text-cyan-100 shadow-[0_0_18px_rgba(34,211,238,.16)]" : "border-white/10 bg-white/[0.03] text-slate-500"}`}><span className="mr-2">{done ? "✓" : active ? "◉" : "○"}</span>{stage.label}</div>{index < runStages.length - 1 && <span className="text-slate-600">→</span>}</div>;
                })}
              </div>
              <p className="mt-4 text-xs text-slate-500">Events received: {events.length}</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="border-white/10 bg-slate-900/75 text-slate-100">
            <CardHeader><CardTitle className="text-base">Plan steps</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {detail.plan?.steps.length ? detail.plan.steps.map((step) => <div key={step.step_id} className="rounded-xl border border-white/8 bg-white/[0.025] p-3"><div className="flex gap-3"><span className="font-mono text-xs text-cyan-300">{step.step_id}</span><div><p className="text-sm font-medium">{step.goal}</p><p className="mt-1 text-xs text-slate-500">{step.args.tool}</p></div></div></div>) : <p className="text-sm text-slate-500">No plan available.</p>}
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-slate-900/75 text-slate-100">
            <CardHeader><CardTitle className="text-base">Tool results</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {detail.results.length ? detail.results.map((result) => <div key={`${result.step_id}-${result.tool}`} className="rounded-xl border border-white/8 bg-white/[0.025] p-3"><div className="flex items-center justify-between gap-3"><span className="text-sm font-medium">{result.tool} · {result.step_id}</span><Badge className={statusTone(result.status)}>{result.status}</Badge></div><p className="mt-2 whitespace-pre-wrap break-words text-sm text-slate-400">{result.output?.kind === "calc" ? String(result.output.value) : result.output?.kind === "search" ? result.output.hits.map((hit) => `${hit.title}: ${hit.snippet}`).join("\n") : result.output?.kind === "kb" ? result.output.passages.map((passage) => passage.text).join("\n") : result.output?.kind === "fetch" ? result.output.text : result.output?.kind === "webhook" ? result.output.summary : result.error?.message ?? "No output"}</p></div>) : <p className="text-sm text-slate-500">No tool results yet.</p>}
            </CardContent>
          </Card>
          <Card className="border-white/10 bg-slate-900/75 text-slate-100">
            <CardHeader><CardTitle className="text-base">Verifier report</CardTitle></CardHeader>
            <CardContent>{detail.report ? <div className="space-y-2"><div className="flex items-center gap-3"><Badge className={statusTone(detail.report.verdict)}>{detail.report.verdict}</Badge><span className="text-sm text-slate-300">Score {(detail.report.score * 100).toFixed(0)}%</span></div><p className="text-sm text-slate-400">{detail.report.feedback}</p></div> : <p className="text-sm text-slate-500">No verifier report yet.</p>}</CardContent>
          </Card>
          <Card className="border-white/10 bg-slate-900/75 text-slate-100">
            <CardHeader><CardTitle className="text-base">Final answer</CardTitle></CardHeader>
            <CardContent>{detail.answer ? <><p className="whitespace-pre-wrap text-sm leading-6 text-slate-300">{detail.answer.answer}</p>{detail.answer.citations.length > 0 && <div className="mt-4 space-y-2 border-t border-white/10 pt-3">{detail.answer.citations.map((citation, index) => <p key={`${citation.step_id}-${index}`} className="text-xs text-slate-500">[{citation.step_id}] {citation.source} — {citation.quote}</p>)}</div>}</> : <p className="text-sm text-slate-500">Answer is not available yet.</p>}</CardContent>
          </Card>
        </div>
      </>}
    </section>
  );
}

export default function Index() {
  const [tab, setTab] = useState<"overview" | "runs" | "tools" | "system">("overview");
  const [query, setQuery] = useState("");
  const [metrics, setMetrics] = useState<Awaited<ReturnType<typeof metricsSummary>> | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [tools, setTools] = useState<ToolSpec[]>([]);
  const [breakers, setBreakers] = useState<Breaker[]>([]);
  const [loading, setLoading] = useState(true);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [breakersLoading, setBreakersLoading] = useState(false);
  const [backendError, setBackendError] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [task, setTask] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const refresh = async () => {
      try {
        const [nextMetrics, nextRuns] = await Promise.all([metricsSummary(), listRuns()]);
        if (!alive) return;
        setMetrics(nextMetrics);
        setRuns(nextRuns);
        setBackendError(false);
      } catch {
        if (alive) setBackendError(true);
      } finally {
        if (alive) setLoading(false);
      }
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (tab !== "tools") return;
    let alive = true;
    setToolsLoading(true);
    void listTools().then((data) => { if (alive) { setTools(data); setBackendError(false); } }).catch(() => { if (alive) setBackendError(true); }).finally(() => { if (alive) setToolsLoading(false); });
    return () => { alive = false; };
  }, [tab]);

  useEffect(() => {
    if (tab !== "system") return;
    let alive = true;
    setBreakersLoading(true);
    void listBreakers().then((data) => { if (alive) { setBreakers(data); setBackendError(false); } }).catch(() => { if (alive) setBackendError(true); }).finally(() => { if (alive) setBreakersLoading(false); });
    return () => { alive = false; };
  }, [tab]);

  const filteredRuns = useMemo(() => runs.filter((run) => `${run.id} ${run.task} ${run.status} ${run.intent ?? ""}`.toLowerCase().includes(query.toLowerCase())), [runs, query]);

  async function submitRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!task.trim()) return;
    setSubmitting(true);
    setSubmitError("");
    try {
      const created = await createRun(task.trim());
      setDialogOpen(false);
      setTask("");
      setSelectedRunId(created.id);
      setTab("runs");
    } catch {
      setSubmitError("Could not create run. Check that the backend is reachable.");
    } finally {
      setSubmitting(false);
    }
  }

  const kpis = metrics ? [
    { label: "Runs today", value: metrics.runs_today.toLocaleString(), icon: Activity, tint: "text-indigo-300" },
    { label: "Success rate", value: `${metrics.success_rate.toFixed(1)}%`, icon: CheckCircle2, tint: "text-emerald-300" },
    { label: "Blocked", value: metrics.blocked_count.toLocaleString(), icon: Shield, tint: "text-rose-300" },
    { label: "Avg latency", value: `${(metrics.avg_latency_ms / 1000).toFixed(2)}s`, icon: Clock3, tint: "text-cyan-300" },
    { label: "Total cost", value: `$${metrics.total_cost_usd.toFixed(4)}`, icon: DollarSign, tint: "text-amber-200" },
    { label: "Active runs", value: metrics.active_runs.toLocaleString(), icon: Play, tint: "text-violet-300" },
  ] : [];

  return (
    <div className="dark min-h-screen bg-[#080d18] text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(59,130,246,.12),transparent_35%),radial-gradient(ellipse_at_top_right,rgba(20,184,166,.08),transparent_32%)]" />
      <div className="relative mx-auto min-h-screen max-w-[1480px] px-4 pb-12 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 py-5">
          <div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl border border-cyan-300/20 bg-cyan-300/10"><Shield className="h-5 w-5 text-cyan-200" /></div><div><p className="text-lg font-semibold tracking-tight">SentryFlow</p><p className="text-xs text-slate-500">Agent orchestration control plane</p></div></div>
          <div className="flex w-full items-center gap-3 sm:w-auto"><div className="relative flex-1 sm:w-64"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" /><Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search runs" className="border-white/10 bg-white/[0.04] pl-9 text-slate-100 placeholder:text-slate-600" /></div><Button onClick={() => setDialogOpen(true)} className="shrink-0 gap-2 bg-cyan-300 text-slate-950 hover:bg-cyan-200"><Plus className="h-4 w-4" /> New Run</Button></div>
        </header>

        <main className="space-y-7 pt-7">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[.22em] text-cyan-300/70">Operations</p><h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Orchestration console</h1><p className="mt-2 text-sm text-slate-400">Monitor governed runs, tool execution, and system resilience.</p></div><div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-400"><span className={`h-2 w-2 rounded-full ${backendError ? "bg-rose-400" : "bg-emerald-400"}`} />{backendError ? "Backend not reachable" : "Live backend"}</div></div>

          {backendError && <div className="flex items-center gap-3 rounded-xl border border-rose-400/20 bg-rose-400/[0.06] p-4 text-sm text-rose-200"><WifiOff className="h-4 w-4 shrink-0" />Backend not reachable. Confirm the API is available at 127.0.0.1:8000.</div>}

          {loading ? <LoadingCards /> : <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{kpis.map((kpi) => <Card key={kpi.label} className="border-white/10 bg-slate-900/70 text-slate-100 shadow-xl shadow-black/10"><CardContent className="flex items-start justify-between p-5"><div><p className="text-sm text-slate-400">{kpi.label}</p><p className="mt-3 text-3xl font-semibold tracking-tight">{kpi.value}</p></div><div className={`rounded-xl bg-white/[0.04] p-2.5 ${kpi.tint}`}><kpi.icon className="h-5 w-5" /></div></CardContent></Card>)}</div>}

          <div className="flex flex-wrap gap-2 border-b border-white/10 pb-3">{(["overview", "runs", "tools", "system"] as const).map((name) => <button key={name} onClick={() => setTab(name)} className={`rounded-lg px-4 py-2 text-sm capitalize transition ${tab === name ? "bg-white/10 text-white" : "text-slate-500 hover:bg-white/[0.04] hover:text-slate-200"}`}>{name}</button>)}</div>

          {selectedRunId && <RunDetailPanel runId={selectedRunId} onBack={() => setSelectedRunId(null)} />}

          {!selectedRunId && tab === "overview" && <div className="grid gap-4 xl:grid-cols-[1.25fr_.75fr]"><Card className="border-white/10 bg-slate-900/70 text-slate-100"><CardHeader><CardTitle className="text-base">Recent runs</CardTitle></CardHeader><CardContent className="space-y-3">{loading ? <><Skeleton className="h-14 bg-white/[0.06]" /><Skeleton className="h-14 bg-white/[0.06]" /></> : runs.length ? runs.slice(0, 5).map((run) => <button key={run.id} onClick={() => { setSelectedRunId(run.id); setTab("runs"); }} className="flex w-full items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] p-3 text-left hover:border-cyan-300/20"><div className="min-w-0"><p className="truncate text-sm font-medium">{run.task}</p><p className="mt-1 truncate font-mono text-[11px] text-slate-500">{run.id}</p></div><Badge className={statusTone(run.status)}>{run.status}</Badge></button>) : <p className="py-6 text-sm text-slate-500">No runs recorded yet.</p>}</CardContent></Card><Card className="border-white/10 bg-slate-900/70 text-slate-100"><CardHeader><CardTitle className="text-base">Runtime snapshot</CardTitle></CardHeader><CardContent className="space-y-4"><div className="flex items-center justify-between rounded-xl bg-white/[0.03] p-4"><div><p className="text-sm text-slate-400">Currently active</p><p className="mt-1 text-2xl font-semibold">{loading ? "—" : metrics?.active_runs.toLocaleString()}</p></div><Activity className="h-5 w-5 text-cyan-300" /></div><div className="flex items-center justify-between rounded-xl bg-white/[0.03] p-4"><div><p className="text-sm text-slate-400">Runs today</p><p className="mt-1 text-2xl font-semibold">{loading ? "—" : metrics?.runs_today.toLocaleString()}</p></div><CheckCircle2 className="h-5 w-5 text-emerald-300" /></div><Button variant="outline" className="w-full border-white/10 bg-transparent text-slate-300 hover:bg-white/5" onClick={() => setTab("runs")}>View run history</Button></CardContent></Card></div>}

          {!selectedRunId && tab === "runs" && <Card className="border-white/10 bg-slate-900/70 text-slate-100"><CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-base">Run history</CardTitle><span className="text-xs text-slate-500">Refreshing every 2 seconds</span></CardHeader><CardContent><div className="overflow-x-auto rounded-xl border border-white/10"><table className="w-full min-w-[720px] text-left text-sm"><thead className="bg-white/[0.035] text-xs uppercase tracking-wider text-slate-500"><tr><th className="p-3 font-medium">Run</th><th className="p-3 font-medium">Task</th><th className="p-3 font-medium">Status</th><th className="p-3 font-medium">Intent</th><th className="p-3 font-medium">Created</th></tr></thead><tbody>{loading ? <tr><td colSpan={5} className="p-4"><Skeleton className="h-10 bg-white/[0.06]" /></td></tr> : filteredRuns.length ? filteredRuns.map((run) => <tr key={run.id} onClick={() => setSelectedRunId(run.id)} className="cursor-pointer border-t border-white/[0.07] hover:bg-white/[0.03]"><td className="p-3 font-mono text-xs text-slate-400">{run.id.slice(0, 8)}</td><td className="max-w-[440px] truncate p-3">{run.task}</td><td className="p-3"><Badge className={statusTone(run.status)}>{run.status}</Badge></td><td className="p-3 text-slate-400">{run.intent ?? "—"}</td><td className="p-3 text-xs text-slate-500">{formatDate(run.created_at)}</td></tr>) : <tr><td colSpan={5} className="p-8 text-center text-slate-500">No matching runs.</td></tr>}</tbody></table></div></CardContent></Card>}

          {!selectedRunId && tab === "tools" && <Card className="border-white/10 bg-slate-900/70 text-slate-100"><CardHeader><CardTitle className="text-base">Tool registry</CardTitle></CardHeader><CardContent>{toolsLoading ? <div className="grid gap-3 md:grid-cols-2">{Array.from({ length: 4 }, (_, i) => <Skeleton key={i} className="h-24 bg-white/[0.06]" />)}</div> : <div className="grid gap-3 md:grid-cols-2">{tools.map((tool) => <ToolCard key={tool.name} tool={tool} />)}{!tools.length && <p className="text-sm text-slate-500">No tools returned by the backend.</p>}</div>}</CardContent></Card>}

          {!selectedRunId && tab === "system" && <Card className="border-white/10 bg-slate-900/70 text-slate-100"><CardHeader><CardTitle className="text-base">Circuit breakers</CardTitle></CardHeader><CardContent className="space-y-3">{breakersLoading ? Array.from({ length: 3 }, (_, i) => <Skeleton key={i} className="h-16 bg-white/[0.06]" />) : breakers.length ? breakers.map((breaker) => <div key={breaker.dependency} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] p-4"><div><p className="font-medium">{breaker.dependency}</p><p className="mt-1 text-xs text-slate-500">Failures: {breaker.failure_count}{breaker.last_failure_at ? ` · Last failure ${formatDate(breaker.last_failure_at)}` : ""}</p></div><Badge className={statusTone(breaker.state)}>{breaker.state}</Badge></div>) : <p className="text-sm text-slate-500">No breaker records returned.</p>}</CardContent></Card>}
        </main>
      </div>

      {dialogOpen && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/75 p-3 backdrop-blur-sm sm:items-center" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialogOpen(false); }}><form onSubmit={submitRun} className="w-full max-w-xl rounded-2xl border border-white/10 bg-slate-900 p-5 shadow-2xl shadow-black/50 sm:p-7"><div className="flex items-start justify-between"><div><p className="text-xs uppercase tracking-[.2em] text-cyan-300/70">New execution</p><h2 className="mt-2 text-xl font-semibold">Start an agent run</h2></div><button type="button" aria-label="Close dialog" onClick={() => setDialogOpen(false)} className="rounded-lg p-2 text-slate-500 hover:bg-white/5 hover:text-white"><X className="h-4 w-4" /></button></div><label htmlFor="task" className="mt-6 block text-sm text-slate-300">Task prompt</label><Textarea id="task" autoFocus value={task} onChange={(event) => setTask(event.target.value)} placeholder="Describe what the agent should do…" className="mt-2 min-h-32 border-white/10 bg-white/[0.03] text-slate-100 placeholder:text-slate-600" /><div className="mt-4"><p className="mb-2 text-xs text-slate-500">Try an example</p><div className="flex flex-wrap gap-2">{examples.map((example) => <button key={example} type="button" onClick={() => setTask(example)} className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-cyan-300/30 hover:text-cyan-100">{example}</button>)}</div></div>{submitError && <p className="mt-3 text-sm text-rose-300">{submitError}</p>}<div className="mt-6 flex justify-end gap-2"><Button type="button" variant="ghost" onClick={() => setDialogOpen(false)} className="text-slate-400">Cancel</Button><Button type="submit" disabled={!task.trim() || submitting} className="gap-2 bg-cyan-300 text-slate-950 hover:bg-cyan-200">{submitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}Run task</Button></div></form></div>}
    </div>
  );
}

function ToolCard({ tool }: { tool: ToolSpec }) {
  const highRisk = tool.risk === "high";
  return <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4"><div className="flex items-start justify-between gap-3"><div className="flex items-center gap-3"><div className={`rounded-xl p-2 ${highRisk ? "bg-rose-400/10 text-rose-300" : "bg-cyan-300/10 text-cyan-200"}`}>{highRisk ? <AlertTriangle className="h-4 w-4" /> : <Activity className="h-4 w-4" />}</div><div><p className="font-medium">{tool.name}</p><p className="mt-1 text-xs text-slate-500">Risk: {tool.risk}</p></div></div><Badge className={highRisk ? statusTone("blocked") : statusTone("completed")}>{highRisk ? "Restricted" : "Available"}</Badge></div><p className="mt-3 text-sm text-slate-400">{tool.description}</p><p className="mt-3 text-xs text-slate-500">Timeout {tool.timeout_seconds}s · Concurrency {tool.max_concurrency}</p></div>;
}
