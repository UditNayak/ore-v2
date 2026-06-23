import { useQuery } from "@tanstack/react-query";
import { getEvalRuns } from "../api/questions";
import type { EvalRun } from "../api/types";
import TrendChart from "../components/TrendChart";

function num(run: EvalRun, key: string): number {
  const v = run.summary[key];
  return typeof v === "number" ? v : 0;
}

function Kpi({
  label,
  value,
  target,
  ok,
}: {
  label: string;
  value: string;
  target: string;
  ok: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div
        className={`text-2xl font-bold ${ok ? "text-emerald-600" : "text-red-600"}`}
      >
        {value}
      </div>
      <div className="text-xs text-slate-400">target {target}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["eval-runs"],
    queryFn: getEvalRuns,
    refetchOnMount: "always", // always re-pull on navigation
    refetchInterval: 15000, // poll so a completed run shows up without a manual reload
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">
            Dashboard — accuracy & learning trends
          </h1>
          <p className="text-slate-500">
            Aggregated from evaluation runs against the success criteria.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
        >
          {isFetching ? "Refreshing…" : "↻ Refresh"}
        </button>
      </header>

      {isLoading && <p className="text-slate-400">Loading…</p>}

      {!isLoading && (!data || data.length === 0) && (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-slate-500">
          No evaluation runs yet. Populate trends by running:
          <pre className="mt-2 rounded bg-slate-800 p-3 text-xs text-slate-100">
            docker compose exec backend python -m app.eval.run_eval --fresh
            --delay 8
          </pre>
        </div>
      )}

      {data && data.length > 0 && <Loaded runs={data} />}
    </div>
  );
}

function Loaded({ runs }: { runs: EvalRun[] }) {
  const latest = runs[runs.length - 1];
  const targets = (latest.summary.targets ?? {}) as unknown as Record<
    string,
    boolean | null
  >;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Kpi
          label="Answer similarity"
          value={num(latest, "v2_similarity").toFixed(2)}
          target="≥ 0.75"
          ok={!!targets.similarity}
        />
        <Kpi
          label="Evidence coverage"
          value={num(latest, "v2_coverage").toFixed(2)}
          target="≥ 0.80"
          ok={!!targets.coverage}
        />
        <Kpi
          label="Learning improvement"
          value={`${(num(latest, "avg_improvement") * 100).toFixed(0)}%`}
          target="≥ 20%"
          ok={!!targets.improvement}
        />
        <Kpi
          label="Max response time"
          value={`${num(latest, "max_response_s").toFixed(1)}s`}
          target="< 15s"
          ok={!!targets.response_time}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <TrendChart
          title="Answer similarity (V2)"
          values={runs.map((r) => num(r, "v2_similarity"))}
          color="#3b82f6"
        />
        <TrendChart
          title="Evidence coverage (V2)"
          values={runs.map((r) => num(r, "v2_coverage"))}
          color="#8b5cf6"
        />
        <TrendChart
          title="Learning improvement"
          values={runs.map((r) => num(r, "avg_improvement"))}
          color="#10b981"
        />
      </div>

      <p className="text-xs text-slate-400">
        {runs.length} run{runs.length === 1 ? "" : "s"} · latest{" "}
        {new Date(latest.created_at).toLocaleString()}
      </p>
    </div>
  );
}
