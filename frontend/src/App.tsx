import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { askQuestion, rerunQuestion, submitHumanAnswer } from "./api/questions";
import type { AnswerView, LearningEventView } from "./api/types";
import AnswerCard from "./components/AnswerCard";
import HumanAnswerForm from "./components/HumanAnswerForm";
import LearningEventCard from "./components/LearningEventCard";

const SAMPLE_QUESTIONS = [
  "Why was release v2.4 delayed?",
  "What caused the checkout latency spike in INC-87?",
  "Who owns the notifications-service?",
  "Why is the notifications-service event-driven?",
  "What is blocking the Reporting v2 milestone?",
];

export default function App() {
  const [text, setText] = useState("");
  const [v1, setV1] = useState<AnswerView | null>(null);
  const [event, setEvent] = useState<LearningEventView | null>(null);
  const [v2, setV2] = useState<AnswerView | null>(null);

  const ask = useMutation({
    mutationFn: askQuestion,
    onSuccess: (a) => {
      setV1(a);
      setEvent(null);
      setV2(null);
    },
  });
  const learn = useMutation({
    mutationFn: (vars: { id: number; answer: string; rootCause: string }) =>
      submitHumanAnswer(vars.id, { answer_text: vars.answer, root_cause: vars.rootCause || undefined }),
    onSuccess: setEvent,
  });
  const rerun = useMutation({ mutationFn: rerunQuestion, onSuccess: setV2 });

  const submit = (q: string) => {
    const t = q.trim();
    if (t) ask.mutate({ text: t, asker: "ui" });
  };

  const delta = v1 && v2 ? Math.round((v2.confidence - v1.confidence) * 100) : null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <header className="mb-6">
          <h1 className="text-2xl font-bold">Organizational Reasoning Engine</h1>
          <p className="text-slate-500">
            Ask a question → review V1 → give the expert answer → re-run to a better V2.
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
            disabled={ask.isPending || !text.trim()}
            className="mt-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {ask.isPending ? "Investigating…" : "Ask"}
          </button>
        </form>

        {ask.isError && <Error msg={(ask.error as Error).message} />}
        {ask.isPending && <Busy text="The agents are planning, investigating, and reasoning…" />}

        {v1 && (
          <div className="space-y-6">
            <Labeled label={v2 ? "Version 1 (before learning)" : "Answer (V1)"}>
              <AnswerCard answer={v1} />
            </Labeled>

            {!event && (
              <HumanAnswerForm
                pending={learn.isPending}
                onSubmit={(answer, rootCause) =>
                  learn.mutate({ id: v1.question_id, answer, rootCause })
                }
              />
            )}
            {learn.isError && <Error msg={(learn.error as Error).message} />}

            {event && (
              <>
                <LearningEventCard event={event} />
                {!v2 && (
                  <button
                    onClick={() => rerun.mutate(v1.question_id)}
                    disabled={rerun.isPending}
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
                  >
                    {rerun.isPending ? "Re-running with memory…" : "Re-run → V2"}
                  </button>
                )}
                {rerun.isError && <Error msg={(rerun.error as Error).message} />}
              </>
            )}

            {v2 && (
              <Labeled
                label={`Version 2 (after learning)${
                  delta != null ? ` — confidence ${delta >= 0 ? "+" : ""}${delta}%` : ""
                }`}
              >
                <AnswerCard answer={v2} />
              </Labeled>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </div>
      {children}
    </div>
  );
}

function Busy({ text }: { text: string }) {
  return <div className="rounded-lg border border-slate-200 bg-white p-6 text-slate-500">{text}</div>;
}

function Error({ msg }: { msg: string }) {
  return <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">Request failed: {msg}</div>;
}
