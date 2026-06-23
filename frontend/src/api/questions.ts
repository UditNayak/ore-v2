import { api } from "./client";
import type { AnswerView, AskRequest } from "./types";

/** Submit a question and get the V1 answer (runs the multi-agent graph server-side). */
export async function askQuestion(payload: AskRequest): Promise<AnswerView> {
  const res = await api.post<AnswerView>("/questions", payload);
  return res.data;
}
