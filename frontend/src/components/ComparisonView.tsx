import type { AnswerView } from "../api/types";
import AnswerColumn from "./AnswerColumn";

interface Props {
  v1: AnswerView;
  v2: AnswerView | null;
  canRerun: boolean;
  rerunPending: boolean;
  onRerun: () => void;
}

/** Side-by-side V1 vs V2 comparison; the right column is a placeholder until V2 exists. */
export default function ComparisonView({
  v1,
  v2,
  canRerun,
  rerunPending,
  onRerun,
}: Props) {
  const delta = v2 ? Math.round((v2.confidence - v1.confidence) * 100) : null;
  const v1Refs = new Set(v1.evidence.map((e) => e.source_ref));
  const newRefs = v2
    ? new Set(
        v2.evidence.map((e) => e.source_ref).filter((r) => !v1Refs.has(r)),
      )
    : undefined;

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <AnswerColumn answer={v1} label="V1 · before learning" accent="slate" />
      {v2 ? (
        <AnswerColumn
          answer={v2}
          label="V2 · after learning"
          accent="emerald"
          delta={delta}
          newRefs={newRefs}
        />
      ) : (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
          <p className="text-sm text-slate-500">
            V2 appears here after you provide the expert answer and re-run.
          </p>
          {canRerun && (
            <button
              onClick={onRerun}
              disabled={rerunPending}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
            >
              {rerunPending ? "Re-running with memory…" : "Re-run → V2"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
