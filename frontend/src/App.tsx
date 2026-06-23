import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { askQuestion } from "./api/questions";
import AnswerCard from "./components/AnswerCard";

// Mirrors docs/TEST_SCENARIOS.md so the corpus can be exercised in one click.
const SAMPLE_QUESTIONS = [
  "Why was release v2.4 delayed?",
  "What caused the checkout latency spike in INC-87?",
  "Who owns the notifications-service?",
  "Why is the notifications-service event-driven?",
  "What is blocking the Reporting v2 milestone?",
];

export default function App() {
  const [text, setText] = useState("");
  const mutation = useMutation({ mutationFn: askQuestion });

  const submit = (question: string) => {
    const q = question.trim();
    if (q) mutation.mutate({ text: q, asker: "ui" });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <header className="mb-6">
          <h1 className="text-2xl font-bold">Organizational Reasoning Engine</h1>
          <p className="text-slate-500">
            Ask an organizational question — the agents investigate the corpus and answer with
            evidence.
          </p>
        </header>

        <div className="mb-3 flex flex-wrap gap-2">
          {SAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => {
                setText(q);
                submit(q);
              }}
              className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-600 hover:bg-slate-100"
            >
              {q}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(text);
          }}
          className="mb-6"
        >
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            placeholder="Ask a question about the organization…"
            className="w-full resize-none rounded-lg border border-slate-300 p-3 focus:border-slate-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={mutation.isPending || !text.trim()}
            className="mt-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {mutation.isPending ? "Investigating…" : "Ask"}
          </button>
        </form>

        {mutation.isError && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            Request failed: {(mutation.error as Error).message}
          </div>
        )}

        {mutation.isPending && (
          <div className="rounded-lg border border-slate-200 bg-white p-6 text-slate-500">
            The agents are planning, investigating sources, and reasoning… this takes a few seconds.
          </div>
        )}

        {mutation.data && <AnswerCard answer={mutation.data} />}
      </div>
    </div>
  );
}
