import type { LearningEventView } from "../api/types";

interface Props {
  event: LearningEventView;
  /** Deterministic gap: expert sources V1 didn't cite (merged with the Critic's). */
  missedSources: string[];
}

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <p className="text-xs text-indigo-800">
      <span className="font-semibold">{label}: </span>
      {children}
    </p>
  );
}

/** Shows the gap analysis (what V1 missed vs the expert) plus the distilled lesson.
 *
 * "Missed sources" uses the deterministic gap (expert's sources minus V1's evidence) — NOT the
 * Critic's free-form list, which can be noisy/duplicated (e.g. "commit d4e5f6a" vs "d4e5f6a").
 */
export default function GapAnalysisCard({ event, missedSources }: Props) {
  return (
    <div className="h-full space-y-2 rounded-xl border border-indigo-200 bg-indigo-50 p-4">
      <h3 className="text-sm font-semibold text-indigo-800">
        🔍 Gap analysis — V1 vs expert
      </h3>

      {missedSources.length > 0 ? (
        <Row label="Missed sources">{missedSources.join(", ")}</Row>
      ) : (
        <Row label="Missed sources">
          none — V1 cited everything the expert used
        </Row>
      )}
      {event.missed_reasoning && (
        <Row label="Missed reasoning">{event.missed_reasoning}</Row>
      )}
      {event.corrected_root_cause && (
        <Row label="Corrected root cause">{event.corrected_root_cause}</Row>
      )}

      <div className="mt-2 rounded-md bg-white/60 p-2">
        <span className="text-xs font-semibold text-indigo-700">
          📘 Lesson:{" "}
        </span>
        <span className="text-sm text-indigo-900">{event.summary}</span>
      </div>
    </div>
  );
}
