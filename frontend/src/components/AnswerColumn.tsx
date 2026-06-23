import type { AnswerMetrics, AnswerView } from "../api/types";
import Collapsible from "./Collapsible";
import ConfidenceBar from "./ConfidenceBar";
import EvidenceList from "./EvidenceList";
import Section from "./Section";

interface Props {
  answer: AnswerView;
  label: string;
  accent: "slate" | "emerald";
  delta?: number | null;
  newRefs?: Set<string>;
  metrics?: AnswerMetrics | null;
}

function ScoreChip({
  label,
  value,
  target,
}: {
  label: string;
  value: number | null;
  target: number;
}) {
  if (value == null) return null;
  const ok = value >= target;
  const cls = ok
    ? "bg-emerald-100 text-emerald-700"
    : "bg-red-100 text-red-700";
  return (
    <span
      className={`rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}
      title={`target ≥ ${target}`}
    >
      {label} {value.toFixed(2)}
    </span>
  );
}

const ACCENT: Record<Props["accent"], string> = {
  slate: "border-slate-200",
  emerald: "border-emerald-300",
};

function DeltaChip({ delta }: { delta: number }) {
  const cls =
    delta > 0
      ? "bg-emerald-100 text-emerald-700"
      : delta < 0
        ? "bg-red-100 text-red-700"
        : "bg-slate-100 text-slate-600";
  const sign = delta > 0 ? "▲ +" : delta < 0 ? "▼ " : "= ";
  return (
    <span className={`rounded px-1.5 py-0.5 text-xs font-semibold ${cls}`}>
      {sign}
      {delta}%
    </span>
  );
}

/** One side of the V1/V2 comparison: header, confidence, answer, root cause, trace, evidence. */
export default function AnswerColumn({
  answer,
  label,
  accent,
  delta,
  newRefs,
  metrics,
}: Props) {
  return (
    <div
      className={`space-y-4 rounded-xl border bg-white p-5 shadow-sm ${ACCENT[accent]}`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-semibold text-slate-700">{label}</span>
        {answer.question_type && (
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
            {answer.question_type}
          </span>
        )}
        {delta != null && <DeltaChip delta={delta} />}
        {answer.elapsed_s != null && (
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
            {answer.elapsed_s}s
          </span>
        )}
        {answer.refused && (
          <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
            refused
          </span>
        )}
      </div>

      {metrics && (
        <div className="flex flex-wrap gap-1.5">
          <ScoreChip label="sim" value={metrics.similarity} target={0.75} />
          <ScoreChip
            label="root-cause"
            value={metrics.root_cause}
            target={0.7}
          />
          <ScoreChip label="coverage" value={metrics.coverage} target={0.8} />
        </div>
      )}

      <ConfidenceBar value={answer.confidence} />

      <Section label="Answer">{answer.answer_text}</Section>
      {answer.root_cause && (
        <Section label="Root cause">{answer.root_cause}</Section>
      )}
      {answer.reasoning_trace.length > 0 && (
        <Collapsible
          title={`Reasoning trace · ${answer.reasoning_trace.length} steps`}
        >
          <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700">
            {answer.reasoning_trace.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </Collapsible>
      )}
      <Collapsible title={`Evidence · ${answer.evidence.length}`}>
        <EvidenceList evidence={answer.evidence} newRefs={newRefs} />
      </Collapsible>
    </div>
  );
}
