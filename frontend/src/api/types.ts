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
  elapsed_s: number | null;
  learning_applied: number;
  model: string | null;
  evidence: EvidenceView[];
}

export interface AgentModel {
  agent: string;
  tier: string;
  provider: string;
  model: string;
}

export interface ModelsView {
  cheap: string;
  smart: string;
  agents: AgentModel[];
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
  expected_sources?: string[];
}

export interface LearningEventView {
  id: number;
  summary: string;
  missed_sources: string[];
  missed_reasoning: string | null;
  corrected_root_cause: string | null;
}

export interface AnswerMetrics {
  similarity: number | null;
  root_cause: number | null;
  coverage: number | null;
  composite: number | null;
}

export interface HumanAnswerView {
  answer_text: string;
  root_cause: string | null;
  expert_name: string | null;
  expected_sources: string[];
}

export interface QuestionDetail {
  id: number;
  text: string;
  status: string;
  question_type: string | null;
  v1: AnswerView | null;
  v2: AnswerView | null;
  v1_metrics: AnswerMetrics | null;
  v2_metrics: AnswerMetrics | null;
  v1_missed_sources: string[];
  human_answer: HumanAnswerView | null;
  learning_event: LearningEventView | null;
}

export interface QuestionListItem {
  id: number;
  text: string;
  status: string;
  question_type: string | null;
  versions: number;
}

export interface EvalRun {
  id: number;
  created_at: string;
  summary: Record<string, number | null>;
}

export interface ScenarioView {
  id: string;
  question: string;
  expert_answer: string;
  expected_root_cause: string | null;
  expected_source_refs: string[];
}
