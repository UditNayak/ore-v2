import { api } from "./client";
import type {
  AnswerView,
  AskRequest,
  EvalRun,
  HumanAnswerRequest,
  LearningEventView,
  QuestionDetail,
  QuestionListItem,
} from "./types";

/** Submit a question and get the V1 answer (runs the multi-agent graph server-side). */
export async function askQuestion(payload: AskRequest): Promise<AnswerView> {
  const res = await api.post<AnswerView>("/questions", payload);
  return res.data;
}

/** Record the expert answer (HITL) and get the resulting gap analysis (learning event). */
export async function submitHumanAnswer(
  questionId: number,
  payload: HumanAnswerRequest,
): Promise<LearningEventView> {
  const res = await api.post<LearningEventView>(
    `/questions/${questionId}/human-answer`,
    payload,
  );
  return res.data;
}

/** Re-run a question with injected memory and get the improved (V2) answer. */
export async function rerunQuestion(questionId: number): Promise<AnswerView> {
  const res = await api.post<AnswerView>(`/questions/${questionId}/rerun`, {});
  return res.data;
}

/** Full learning-loop view of a question (V1, expert answer, lesson, V2, live metrics). */
export async function getQuestionDetail(
  questionId: number,
): Promise<QuestionDetail> {
  const res = await api.get<QuestionDetail>(`/questions/${questionId}`);
  return res.data;
}

/** Recent questions (the feed). */
export async function listQuestions(): Promise<QuestionListItem[]> {
  const res = await api.get<QuestionListItem[]>("/questions");
  return res.data;
}

/** Eval-run history for the dashboard trends. */
export async function getEvalRuns(): Promise<EvalRun[]> {
  const res = await api.get<EvalRun[]>("/metrics/eval-runs");
  return res.data;
}
