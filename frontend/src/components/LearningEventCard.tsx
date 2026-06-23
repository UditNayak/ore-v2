import type { LearningEventView } from "../api/types";

/** Shows the gap analysis (learning event) the Critic produced from the expert answer. */
export default function LearningEventCard({ event }: { event: LearningEventView }) {
  return (
    <div className="space-y-3 rounded-xl border border-indigo-200 bg-indigo-50 p-5">
      <h3 className="font-semibold text-indigo-800">📘 Learning event (what V1 missed)</h3>
      <div>
        <span className="text-sm font-semibold text-indigo-700">Lesson: </span>
        <span className="text-sm text-indigo-900">{event.summary}</span>
      </div>
      {event.corrected_root_cause && (
        <div className="text-sm">
          <span className="font-semibold text-indigo-700">Corrected root cause: </span>
          {event.corrected_root_cause}
        </div>
      )}
      {event.missed_reasoning && (
        <div className="text-sm">
          <span className="font-semibold text-indigo-700">Missed reasoning: </span>
          {event.missed_reasoning}
        </div>
      )}
      {event.missed_sources.length > 0 && (
        <div className="text-sm">
          <span className="font-semibold text-indigo-700">Missed sources: </span>
          {event.missed_sources.join(", ")}
        </div>
      )}
    </div>
  );
}
