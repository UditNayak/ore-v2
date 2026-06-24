import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  askQuestion,
  getQuestionDetail,
  rerunQuestion,
  submitHumanAnswer,
} from "../api/questions";
import ComparisonView from "../components/ComparisonView";
import Feed from "../components/Feed";
import HumanAnswerForm from "../components/HumanAnswerForm";
import LearningEventCard from "../components/LearningEventCard";
import Stepper from "../components/Stepper";

const SAMPLE_QUESTIONS = [
  "Why was release v2.4 delayed?",
  "What caused the checkout latency spike in INC-87?",
  "Who owns the notifications-service?",
  "Why is the notifications-service event-driven?",
  "What is blocking the Reporting v2 milestone?",
];

export default function AskPage() {
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const [questionId, setQuestionId] = useState<number | null>(null);

  const detail = useQuery({
    queryKey: ["question", questionId],
    queryFn: () => getQuestionDetail(questionId as number),
    enabled: questionId != null,
  });

  const refetchAll = () => {
    qc.invalidateQueries({ queryKey: ["question", questionId] });
    qc.invalidateQueries({ queryKey: ["questions"] });
  };

  const ask = useMutation({
    mutationFn: askQuestion,
    onSuccess: (a) => {
      setQuestionId(a.question_id);
      qc.invalidateQueries({ queryKey: ["questions"] });
    },
  });
  const learn = useMutation({
    mutationFn: (vars: {
      id: number;
      answer: string;
      rootCause: string;
      sources: string[];
    }) =>
      submitHumanAnswer(vars.id, {
        answer_text: vars.answer,
        root_cause: vars.rootCause || undefined,
        expected_sources: vars.sources,
      }),
    onSuccess: refetchAll,
  });
  const rerun = useMutation({
    mutationFn: rerunQuestion,
    onSuccess: refetchAll,
  });

  const submit = (q: string) => {
    const t = q.trim();
    if (t) ask.mutate({ text: t, asker: "ui" });
  };
  const reset = () => {
    setQuestionId(null);
    setText("");
  };

  const d = detail.data;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">Organizational Reasoning Engine</h1>
        <p className="text-slate-500">
          Ask → review V1 → give the expert answer → re-run to a measurably
          better V2.
        </p>
      </header>

      {questionId == null ? (
        <>
          <div className="mb-3 flex flex-wrap gap-2">
            {SAMPLE_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => submit(q)}
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
            <p className="text-slate-800">{d?.text ?? "…"}</p>
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
      {(ask.isPending || (questionId != null && detail.isLoading)) && (
        <Busy text="The agents are planning, investigating, and reasoning…" />
      )}

      {d?.v1 && (
        <div className="space-y-5">
          <Stepper
            hasV1={!!d.v1}
            hasEvent={!!d.learning_event}
            hasV2={!!d.v2}
          />

          {d.learning_event ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="h-full space-y-1 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <h3 className="text-sm font-semibold text-amber-800">
                  🧑 Expert answer
                </h3>
                <p className="text-sm text-amber-900">
                  {d.human_answer?.answer_text}
                </p>
                {d.human_answer &&
                  d.human_answer.expected_sources.length > 0 && (
                    <p className="text-xs text-amber-700">
                      Sources: {d.human_answer.expected_sources.join(", ")}
                    </p>
                  )}
              </div>
              <LearningEventCard event={d.learning_event} />
            </div>
          ) : (
            <HumanAnswerForm
              pending={learn.isPending}
              onSubmit={(answer, rootCause, sources) =>
                learn.mutate({ id: d.id, answer, rootCause, sources })
              }
            />
          )}
          {learn.isError && <Banner msg={(learn.error as Error).message} />}
          {rerun.isError && <Banner msg={(rerun.error as Error).message} />}

          <ComparisonView
            v1={d.v1}
            v2={d.v2}
            v1Metrics={d.v1_metrics}
            v2Metrics={d.v2_metrics}
            canRerun={!!d.learning_event}
            rerunPending={rerun.isPending}
            onRerun={() => rerun.mutate(d.id)}
          />
        </div>
      )}

      <section className="mt-10">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Recent questions
        </h2>
        <Feed activeId={questionId} onSelect={setQuestionId} />
      </section>
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
