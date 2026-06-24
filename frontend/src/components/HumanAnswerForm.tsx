import { useState } from "react";

interface Props {
  pending: boolean;
  onSubmit: (
    answerText: string,
    rootCause: string,
    expectedSources: string[],
  ) => void;
}

/** Capture the expert ground-truth answer (the HITL step that drives learning). */
export default function HumanAnswerForm({ pending, onSubmit }: Props) {
  const [answer, setAnswer] = useState("");
  const [rootCause, setRootCause] = useState("");
  const [sources, setSources] = useState("");

  const parseSources = (raw: string): string[] =>
    raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (answer.trim())
          onSubmit(answer.trim(), rootCause.trim(), parseSources(sources));
      }}
      className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-5"
    >
      <div>
        <h3 className="font-semibold text-amber-800">
          🧑 Expert answer (ground truth)
        </h3>
        <p className="text-sm text-amber-700">
          Provide the real answer — the Critic compares it to V1 and captures
          what was missed.
        </p>
      </div>
      <textarea
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        rows={3}
        placeholder="The expert's answer…"
        className="w-full resize-none rounded-lg border border-amber-300 p-2 focus:outline-none"
      />
      <input
        value={rootCause}
        onChange={(e) => setRootCause(e.target.value)}
        placeholder="Root cause (optional)"
        className="w-full rounded-lg border border-amber-300 p-2 focus:outline-none"
      />
      <div>
        <input
          value={sources}
          onChange={(e) => setSources(e.target.value)}
          placeholder="Sources you used, comma-separated (e.g. NIM-412, a1b2c3d, t-rel-1)"
          className="w-full rounded-lg border border-amber-300 p-2 focus:outline-none"
        />
        <p className="mt-1 text-xs text-amber-600">
          Used to score <strong>evidence coverage</strong> — issue keys, commit
          shas, or slack thread ids.
        </p>
      </div>
      <button
        type="submit"
        disabled={pending || !answer.trim()}
        className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
      >
        {pending ? "Analyzing gap…" : "Submit expert answer"}
      </button>
    </form>
  );
}
