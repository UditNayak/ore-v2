import { api } from "./client";
import type { AnswerView, AskRequest, HumanAnswerRequest, LearningEventView } from "./types";

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
  const res = await api.post<LearningEventView>(`/questions/${questionId}/human-answer`, payload);
  return res.data;
}

/** Re-run a question with injected memory and get the improved (V2) answer. */
export async function rerunQuestion(questionId: number): Promise<AnswerView> {
  const res = await api.post<AnswerView>(`/questions/${questionId}/rerun`, {});
  return res.data;
}
