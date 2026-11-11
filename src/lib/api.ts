const API_BASE = "http://127.0.0.1:8000/api/v1";

export type RunSummary = {
  id: string;
  task: string;
  status: string;
  intent: string | null;
  verdict: string | null;
  verifier_score: number | null;
  budget: { cost_usd: number; elapsed_ms: number; steps_executed: number };
  created_at: string;
  completed_at: string | null;
};

export type PlanStep = {
  step_id: string;
  goal: string;
  args: { tool: string; [key: string]: unknown };
  depends_on: string[];
};

export type ToolResult = {
  step_id: string;
  tool: string;
  status: string;
  output:
    | { kind: "search"; hits: { title: string; url: string; snippet: string }[] }
    | { kind: "fetch"; url: string; text: string; truncated: boolean }
    | { kind: "calc"; value: number }
    | { kind: "kb"; passages: { doc_id: string; text: string; score: number }[] }
    | { kind: "webhook"; status_code: number; summary: string }
    | null;
  error: { code: string; message: string } | null;
  latency_ms: number;
  cache_hit: boolean;
};

export type RunDetail = RunSummary & {
  plan: { steps: PlanStep[]; strategy_summary: string; risk: string } | null;
  results: ToolResult[];
  answer: { answer: string; citations: { step_id: string; source: string; quote: string }[]; confidence: number; degraded: boolean } | null;
  report: { verdict: string; score: number; feedback: string; safe_message: string | null } | null;
  error: { code: string; message: string } | null;
};

export type ToolSpec = {
  name: string;
  description: string;
  risk: string;
  capabilities: string[];
  cacheable: boolean;
  cache_ttl_seconds: number;
  timeout_seconds: number;
  max_concurrency: number;
};

export type Breaker = {
  dependency: string;
  state: "closed" | "open" | "half_open";
  failure_count: number;
  last_failure_at: string | null;
  opens_at: string | null;
};

export type MetricsSummary = {
  runs_today: number;
  success_rate: number;
  blocked_count: number;
  avg_latency_ms: number;
  active_runs: number;
  total_cost_usd: number;
};

export type RunEvent = {
  seq: number;
  run_id: string;
  type: string;
  timestamp: string;
  node?: string;
  status?: string;
  error?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new Error(`API request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export const listRuns = (): Promise<RunSummary[]> => request("/runs");
export const createRun = (task: string): Promise<RunSummary> =>
  request("/runs", { method: "POST", body: JSON.stringify({ task }) });
export const getRun = (id: string): Promise<RunDetail> => request(`/runs/${encodeURIComponent(id)}`);
export const getRunEvents = async (id: string, afterSeq = 0): Promise<RunEvent[]> => {
  const result = await request<{ events: RunEvent[] }>(`/runs/${encodeURIComponent(id)}/events?after_seq=${afterSeq}`);
  return result.events;
};
export const listTools = (): Promise<ToolSpec[]> => request("/tools");
export const listBreakers = (): Promise<Breaker[]> => request("/system/breakers");
export const metricsSummary = (): Promise<MetricsSummary> => request("/system/metrics/summary");
