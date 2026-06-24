import type { LearningEventView } from "../api/types";

/** Shows the gap analysis (learning event) the Critic produced from the expert answer. */
export default function LearningEventCard({
  event,
}: {
  event: LearningEventView;
}) {
  return (
    <div className="h-full space-y-2 rounded-xl border border-indigo-200 bg-indigo-50 p-4">
      <h3 className="text-sm font-semibold text-indigo-800">
        📘 Lesson — what V1 missed
      </h3>
      <p className="text-sm text-indigo-900">{event.summary}</p>
      {event.corrected_root_cause && (
        <p className="text-xs text-indigo-800">
          <span className="font-semibold">Corrected root cause: </span>
          {event.corrected_root_cause}
        </p>
      )}
      {event.missed_reasoning && (
        <p className="text-xs text-indigo-800">
          <span className="font-semibold">Missed reasoning: </span>
          {event.missed_reasoning}
        </p>
      )}
      {event.missed_sources.length > 0 && (
        <p className="text-xs text-indigo-800">
          <span className="font-semibold">Missed sources: </span>
          {event.missed_sources.join(", ")}
        </p>
      )}
    </div>
  );
}
