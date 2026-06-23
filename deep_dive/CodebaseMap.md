# ORE — Components Catalog

A complete map of every component in the codebase, grouped by layer, with its file, purpose, and key
symbols. This is the index for the deep dive: pick any row and go deeper from there.

**Layered request flow:** `api → services → agents (LangGraph) → tools / rag / learning → llm gateway`,
all over **Postgres + pgvector**. Frontend (React) talks to the API over HTTP.

---

## 1. Core (`backend/app/core/`) — cross-cutting foundation
| File | Purpose | Key symbols |
|---|---|---|
| `config.py` | Typed settings from env/.env (one source of truth for all knobs) | `Settings` (pydantic-settings), `get_settings()` (lru_cached) |
| `enums.py` | Controlled vocabularies stored as strings (DRY) | `SourceType`, `DocType`, `QuestionType`, `QuestionStatus`, `IssueStatus` |
| `guardrails.py` | Pure guardrail functions | `filter_relevant()` (relevance floor), `evaluate_answer()` (confidence + grounding), `INSUFFICIENT_EVIDENCE_MESSAGE` |
| `logging.py` | Structured JSON logging setup | `configure_logging()` (structlog) |
| `observability.py` | Env-gated LangSmith tracing | `configure_observability()` |

## 2. LLM gateway (`backend/app/llm/`) — provider-agnostic model access
| File | Purpose | Key symbols |
|---|---|---|
| `tiers.py` | Capability tiers (intent, not model) | `Tier` (CHEAP, SMART) |
| `config.py` | Typed schema + loader for `config/llm.yaml` | `CandidateConfig`, `LLMConfig`, `load_llm_config()` |
| `gateway.py` | Resolve a tier → fallback-composed runnable; cost tiers + failover | `LLMGateway`, `get_llm()`, `primary_model()`, `get_gateway()` (singleton), `_build_litellm_chat()` |
| `structured.py` | Provider-agnostic JSON structured output (works across fallbacks) | `structured_call()` |
| `metrics.py` | Per-LLM-call observability callback | `LLMMetricsCallback` (model, latency, tokens, cost, fallback) |
| `smoke.py` | Live smoke test of both tiers | `python -m app.llm.smoke` |

## 3. Database (`backend/app/db/`) — persistence (Postgres + pgvector)
| File | Purpose | Key symbols |
|---|---|---|
| `base.py` | Declarative base + shared columns | `Base`, `created_at_column()` |
| `models.py` | All ORM models | corpus: `Document`, `DocumentChunk`, `Issue`, `SlackMessage`, `Commit`; runtime: `Question`, `AIAnswer`, `AnswerEvidence`, `HumanAnswer`, `LearningEvent`, `EvalRun` |
| `session.py` | Async engine + session factory | `engine`, `SessionLocal`, `get_session()` (FastAPI dep) |
| `migrate.py` | Programmatic Alembic upgrade (runs on startup) | `run_migrations()` |
| `seed.py` | Idempotent corpus seeding + reseed | `seed_if_empty()`, `reseed()`; `python -m app.db.seed --force` |
| `reset.py` | Fresh start: clear questions/lessons/eval runs (keep corpus) | `reset_runtime()`; `python -m app.db.reset` |
| `alembic/versions/0001_initial.py` | pgvector extension + all tables + HNSW indexes | — |
| `alembic/versions/0002_eval_runs.py` | `eval_runs` table | — |
| `alembic/versions/0003_human_answer_expected_sources.py` | `human_answers.expected_sources` | — |

## 4. RAG (`backend/app/rag/`) — embeddings + ingestion
| File | Purpose | Key symbols |
|---|---|---|
| `embeddings.py` | fastembed BGE-small (CPU, no key); asymmetric query/doc | `embed_documents()`, `embed_query()`, `_model()` |
| `ingest.py` | Chunk + embed documents into pgvector | `chunk_text()`, `ingest_document()`, `CHUNK_SIZE`, `CHUNK_OVERLAP` |

## 5. Tools (`backend/app/tools/`) — the four evidence sources
| File | Purpose | Key symbols |
|---|---|---|
| `schemas.py` | Uniform evidence object | `Evidence` |
| `doc_search.py` | Semantic RAG over chunks (pgvector cosine) | `search_docs()` |
| `issue_search.py` | Structured + keyword over issues | `search_issues()` |
| `slack_search.py` | Keyword over chat messages | `search_slack()` |
| `commit_search.py` | Keyword + service filter over commits | `search_commits()` |
| `keyword.py` | Shared lexical helpers (DRY) | `terms()`, `ilike_any()`, `keyword_score()` |

## 6. Agents (`backend/app/agents/`) — the LangGraph brain
| File | Purpose | Key symbols |
|---|---|---|
| `state.py` | Shared graph state threaded through all nodes | `GraphState` |
| `schemas.py` | Typed agent hand-offs | `PlannerOutput`, `SufficiencyVerdict`, `ReasonerOutput`, `CriticOutput` |
| `graph.py` | Wire + compile the graph; loop controller | `build_graph()`, `get_graph()`, `route_after_investigation()` |
| `nodes/planner.py` | Classify question + pick sources (CHEAP) | `planner()`, `_normalize_question_type()` |
| `nodes/investigator.py` | Agentic retrieval loop: query → judge → loop/broaden (CHEAP) | `investigator()` |
| `nodes/reasoner.py` | Synthesize answer + trace + root cause + confidence (SMART) | `reasoner()` |
| `nodes/common.py` | Per-request context + tool dispatch + evidence helpers | `context()`, `run_tool()`, `dedup_evidence()`, `format_evidence()`, `format_evidence_brief()`, `SEARCHABLE_SOURCES`, `TOOLS` |

## 7. Learning loop (`backend/app/learning/`) — what makes V2 better
| File | Purpose | Key symbols |
|---|---|---|
| `critic.py` | Gap analysis V1 vs expert (SMART) | `run_critic()` |
| `store.py` | Persist + retrieve learning events (pgvector memory) | `create_learning_event()`, `retrieve_learning_context()` |
| `injection.py` | Format lessons for prompt injection | `format_learning_event()`, `learning_block()`, `LEARNING_PREAMBLE` |

## 8. Evaluation (`backend/app/eval/`) — success-criteria measurement
| File | Purpose | Key symbols |
|---|---|---|
| `scenarios.py` | Load qa_scenarios.json | `Scenario`, `load_scenarios()` |
| `metrics.py` | Pure metrics + targets + aggregate | `cosine()`, `text_similarity()`, `evidence_coverage()`, `composite_accuracy()`, `improvement()` (gap-closed), `build_summary()`, `TARGET_*` |
| `judge.py` | LLM-as-judge for root cause (SMART, embedding fallback) | `judge_root_cause()`, `RootCauseVerdict` |
| `runner.py` | Run scenarios end-to-end (V1→expert→V2), score, persist, report | `run_eval()`, `_run_scenario()`, `_score()` |
| `run_eval.py` | CLI | `python -m app.eval.run_eval` (`--limit/--scenario/--fresh/--delay`) |

## 9. Services (`backend/app/services/`) — orchestration + persistence
| File | Purpose | Key symbols |
|---|---|---|
| `reasoning.py` | Run the graph, persist answers, stamp models | `answer_question()` (V1), `rerun_question()` (V2), `get_answer()` |
| `learning.py` | HITL capture + Critic + learning event | `submit_human_answer()`, `get_learning_event()` |
| `scoring.py` | Live per-question scoring vs the human answer | `score_answer()`, `evidence_ids()` |
| `questions.py` | Question feed + full learning-loop detail | `load_question_detail()`, `list_recent_questions()`, `QuestionDetail` |
| `metrics.py` | Read eval runs + record a Dashboard point on loop completion | `list_eval_runs()`, `record_question_run()` |

## 10. API (`backend/app/api/`) — thin FastAPI routers
| File | Purpose | Key endpoints |
|---|---|---|
| `schemas.py` | Request/response models | `AskRequest`, `AnswerView`, `HumanAnswerRequest`, `LearningEventView`, `QuestionDetailView`, `AnswerMetricsView`, `QuestionListItem`, `EvalRunView`, `ScenarioView`, `ModelsView` |
| `questions.py` | The learning loop | `POST /questions`, `GET /questions`, `GET /questions/{id}`, `POST /{id}/human-answer`, `POST /{id}/rerun`, `GET /questions/answers/{id}` |
| `metrics.py` | Dashboard data | `GET /metrics/eval-runs` |
| `scenarios.py` | Seeded ground truth (autoload) | `GET /scenarios` |
| `models.py` | Model-per-agent legend | `GET /models` |
| `health.py` | Liveness | `GET /health` |
| `main.py` (app root) | App factory, lifespan (migrate + seed), router wiring, CORS | `app`, `lifespan` |

## 11. Data (`backend/app/data/`) — synthetic "Nimbus" corpus
| File | Purpose |
|---|---|
| `seed/documents.json` | Wiki / postmortems / design docs |
| `seed/issues.json` | Issue tracker tickets (NIM-*) |
| `seed/slack.json` | Slack-style threads (the largest source) |
| `seed/commits.json` | Commit history |
| `qa_scenarios.json` | Test scenarios: question + expert answer + expected root cause + expected sources |

## 12. Frontend (`frontend/src/`) — React + Vite + TS + Tailwind
| File | Purpose |
|---|---|
| `App.tsx` | Router shell (TopNav + Sidebar + routes `/`, `/q/:id`, `/dashboard`) |
| `main.tsx` | Entry + React Query provider |
| `api/client.ts` | Axios instance (base URL) |
| `api/types.ts` | TypeScript types mirroring backend schemas |
| `api/questions.ts` | API calls: `askQuestion`, `submitHumanAnswer`, `rerunQuestion`, `getQuestionDetail`, `listQuestions`, `getEvalRuns`, `getScenarios`, `getModels` |
| `pages/AskPage.tsx` | The learning-loop workspace (dropdown/free-text, V1/V2, gap, models legend) |
| `pages/DashboardPage.tsx` | KPI tiles + trend charts (auto-refresh) |
| `components/TopNav.tsx` | Top nav (Ask / Dashboard) |
| `components/Sidebar.tsx` | Collapsible, persisted Recent-questions sidebar |
| `components/Feed.tsx` | Recent-questions list (links to `/q/:id`) |
| `components/ComparisonView.tsx` | Side-by-side V1 vs V2 grid |
| `components/AnswerColumn.tsx` | One answer column (confidence, metric chips, model badge, sections) |
| `components/Collapsible.tsx` | Disclosure (collapsed by default) for trace/evidence |
| `components/EvidenceList.tsx` | Evidence items + "new" markers |
| `components/SourceBadge.tsx` | Source-type colored pill |
| `components/Section.tsx` | Labeled section |
| `components/ConfidenceBar.tsx` | Confidence meter |
| `components/Stepper.tsx` | 4-step loop progress |
| `components/HumanAnswerForm.tsx` | Expert answer form + autoload + sources |
| `components/GapAnalysisCard.tsx` | What V1 missed (deterministic gap) + lesson |
| `components/ModelsLegend.tsx` | Agents → models legend |
| `components/TrendChart.tsx` | Dependency-free SVG trend line |

## 13. Infra & config (repo root + backend)
| File | Purpose |
|---|---|
| `config/llm.yaml` | Provider/model tiers (currently Claude Sonnet/Haiku + Groq fallback) |
| `docker-compose.yaml` | backend + frontend + Postgres(pgvector) |
| `backend/Dockerfile`, `frontend/Dockerfile` | Container builds |
| `backend/pyproject.toml` | Deps + Ruff/mypy/pytest config |
| `backend/alembic.ini` | Alembic config |
| `.env.example` | All environment variables |

## 14. Tests (`backend/tests/`)
| File | Covers |
|---|---|
| `test_llm_gateway.py` | Tier parsing + fallback |
| `test_embeddings.py` | Embedding dim + chunking |
| `test_tools.py` | The four tools vs the seeded corpus |
| `test_routing.py` | `route_after_investigation` loop control |
| `test_guardrails.py` | Relevance filter, confidence, grounding |
| `test_nodes.py` | Reasoner refusal without evidence |
| `test_learning.py` | Learning-event pgvector roundtrip + injection |
| `test_eval_metrics.py` | similarity / coverage / composite / improvement |
| `test_eval_judge.py` | LLM judge short-circuit + embedding fallback |

---

## How to go deeper from here
Suggested follow-up deep-dive files in this folder, one concern each:
- `AgentGraph.md` — the LangGraph: state, nodes, edges, the loop, broadening.
- `Retrieval.md` — the four tools + the agentic loop + relevance filtering.
- `LearningLoop.md` — Critic → memory → injection → V2 (with a worked example).
- `LLMGateway.md` — tiers, fallback, structured output, cost capture.
- `Evaluation.md` — metrics, the LLM judge, gap-closed improvement, the dashboard pipeline.
- `DataModel.md` — the schema, relationships, and the runtime vs corpus split.
