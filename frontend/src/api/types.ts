// Mirrors the backend AnswerView (app/api/schemas.py).

export interface EvidenceView {
  source_type: string;
  source_ref: string;
  title: string | null;
  snippet: string;
  score: number | null;
}

export interface AnswerView {
  answer_id: number;
  question_id: number;
  question: string;
  version: number;
  question_type: string | null;
  answer_text: string;
  root_cause: string | null;
  confidence: number;
  reasoning_trace: string[];
  refused: boolean;
  refusal_reason: string | null;
  cited_source_refs: string[];
  evidence: EvidenceView[];
}

export interface AskRequest {
  text: string;
  asker?: string;
  channel?: string;
}

export interface HumanAnswerRequest {
  answer_text: string;
  root_cause?: string;
  expert_name?: string;
}

export interface LearningEventView {
  id: number;
  summary: string;
  missed_sources: string[];
  missed_reasoning: string | null;
  corrected_root_cause: string | null;
}
