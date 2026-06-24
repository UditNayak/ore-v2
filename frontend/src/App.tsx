import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { askQuestion, rerunQuestion, submitHumanAnswer } from "./api/questions";
import type { AnswerView, LearningEventView } from "./api/types";
import ComparisonView from "./components/ComparisonView";
import HumanAnswerForm from "./components/HumanAnswerForm";
import LearningEventCard from "./components/LearningEventCard";
import Stepper from "./components/Stepper";

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
  const [expertText, setExpertText] = useState("");

  const reset = () => {
    setV1(null);
    setEvent(null);
    setV2(null);
    setExpertText("");
    setText("");
  };

  const ask = useMutation({
    mutationFn: askQuestion,
    onSuccess: (a) => {
      setV1(a);
      setEvent(null);
      setV2(null);
      setExpertText("");
    },
  });
  const learn = useMutation({
    mutationFn: (vars: { id: number; answer: string; rootCause: string }) =>
      submitHumanAnswer(vars.id, {
        answer_text: vars.answer,
        root_cause: vars.rootCause || undefined,
      }),
    onSuccess: setEvent,
  });
  const rerun = useMutation({ mutationFn: rerunQuestion, onSuccess: setV2 });

  const submit = (q: string) => {
    const t = q.trim();
    if (t) ask.mutate({ text: t, asker: "ui" });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-bold">
            Organizational Reasoning Engine
          </h1>
          <p className="text-slate-500">
            Ask a question → review V1 → give the expert answer → re-run to a
            measurably better V2.
          </p>
        </header>

        {!v1 ? (
          <>
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
          </>
        ) : (
          <div className="mb-5 flex items-start justify-between gap-4 rounded-lg border border-slate-200 bg-white p-3">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Question
              </span>
              <p className="text-slate-800">{v1.question}</p>
            </div>
            <button
              onClick={reset}
              className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
            >
              Ask another
            </button>
          </div>
        )}

        {ask.isError && <Banner msg={(ask.error as Error).message} />}
        {ask.isPending && (
          <Busy text="The agents are planning, investigating, and reasoning…" />
        )}

        {v1 && (
          <div className="space-y-5">
            <Stepper hasV1={!!v1} hasEvent={!!event} hasV2={!!v2} />

            {/* Band: expert answer + lesson, or the expert-answer form */}
            {event ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="h-full space-y-1 rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <h3 className="text-sm font-semibold text-amber-800">
                    🧑 Expert answer
                  </h3>
                  <p className="text-sm text-amber-900">{expertText}</p>
                </div>
                <LearningEventCard event={event} />
              </div>
            ) : (
              <HumanAnswerForm
                pending={learn.isPending}
                onSubmit={(answer, rootCause) => {
                  setExpertText(answer);
                  learn.mutate({ id: v1.question_id, answer, rootCause });
                }}
              />
            )}
            {learn.isError && <Banner msg={(learn.error as Error).message} />}
            {rerun.isError && <Banner msg={(rerun.error as Error).message} />}

            <ComparisonView
              v1={v1}
              v2={v2}
              canRerun={!!event}
              rerunPending={rerun.isPending}
              onRerun={() => rerun.mutate(v1.question_id)}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function Busy({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 text-slate-500">
      {text}
    </div>
  );
}

function Banner({ msg }: { msg: string }) {
  return (
    <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
      Request failed: {msg}
    </div>
  );
}
