import type { AnswerView, EvidenceView } from "../api/types";
import ConfidenceBar from "./ConfidenceBar";

const SOURCE_COLORS: Record<string, string> = {
  doc: "bg-blue-100 text-blue-700",
  issue: "bg-purple-100 text-purple-700",
  slack: "bg-green-100 text-green-700",
  commit: "bg-orange-100 text-orange-700",
  learning: "bg-pink-100 text-pink-700",
};

function SourceBadge({ type }: { type: string }) {
  const cls = SOURCE_COLORS[type] ?? "bg-slate-100 text-slate-700";
  return <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>{type}</span>;
}

function EvidenceRow({ e }: { e: EvidenceView }) {
  return (
    <li className="rounded-md border border-slate-200 bg-white p-3">
      <div className="mb-1 flex items-center gap-2 text-sm">
        <SourceBadge type={e.source_type} />
        <span className="font-mono text-xs text-slate-500">{e.source_ref}</span>
        {e.score != null && (
          <span className="ml-auto text-xs text-slate-400">score {e.score.toFixed(2)}</span>
        )}
      </div>
      {e.title && <div className="text-sm font-medium text-slate-700">{e.title}</div>}
      <p className="mt-1 line-clamp-3 text-sm text-slate-600">{e.snippet}</p>
    </li>
  );
}

/** Renders a V1 answer: verdict, confidence, root cause, reasoning trace, and evidence. */
export default function AnswerCard({ answer }: { answer: AnswerView }) {
  return (
    <div className="space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        {answer.question_type && (
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
            {answer.question_type}
          </span>
        )}
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
          V{answer.version}
        </span>
        {answer.refused && (
          <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
            refused: {answer.refusal_reason}
          </span>
        )}
      </div>

      <ConfidenceBar value={answer.confidence} />

      <div>
        <h3 className="text-sm font-semibold text-slate-500">Answer</h3>
        <p className="mt-1 text-slate-800">{answer.answer_text}</p>
      </div>

      {answer.root_cause && (
        <div>
          <h3 className="text-sm font-semibold text-slate-500">Root cause</h3>
          <p className="mt-1 text-slate-800">{answer.root_cause}</p>
        </div>
      )}

      {answer.reasoning_trace.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-500">Reasoning trace</h3>
          <ol className="mt-1 list-decimal space-y-1 pl-5 text-sm text-slate-700">
            {answer.reasoning_trace.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      <div>
        <h3 className="text-sm font-semibold text-slate-500">
          Evidence ({answer.evidence.length})
        </h3>
        <ul className="mt-2 space-y-2">
          {answer.evidence.map((e) => (
            <EvidenceRow key={`${e.source_type}:${e.source_ref}`} e={e} />
          ))}
        </ul>
      </div>
    </div>
  );
}
