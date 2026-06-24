import type { EvidenceView } from "../api/types";
import SourceBadge from "./SourceBadge";

interface Props {
  evidence: EvidenceView[];
  /** source_refs that are new in this version (vs the other) — marked "new". */
  newRefs?: Set<string>;
}

/** Renders a list of evidence items, optionally flagging ones new to this version. */
export default function EvidenceList({ evidence, newRefs }: Props) {
  return (
    <ul className="space-y-2">
      {evidence.map((e) => (
        <li
          key={`${e.source_type}:${e.source_ref}`}
          className="rounded-md border border-slate-200 bg-white p-2.5"
        >
          <div className="mb-1 flex items-center gap-2 text-xs">
            <SourceBadge type={e.source_type} />
            <span className="font-mono text-slate-500">{e.source_ref}</span>
            {newRefs?.has(e.source_ref) && (
              <span className="rounded bg-emerald-100 px-1.5 py-0.5 font-medium text-emerald-700">
                new
              </span>
            )}
            {e.score != null && (
              <span className="ml-auto text-slate-400">
                {e.score.toFixed(2)}
              </span>
            )}
          </div>
          {e.title && (
            <div className="text-xs font-medium text-slate-700">{e.title}</div>
          )}
          <p className="mt-0.5 line-clamp-3 text-xs text-slate-600">
            {e.snippet}
          </p>
        </li>
      ))}
    </ul>
  );
}
