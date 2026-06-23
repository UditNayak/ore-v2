# ORE — Agentic Components

A deep look at the **agents** that make up the system — what each one does, the model it runs on, what
it reads and writes, how it decides, and why it's designed that way. (For the code/file map, see
`CodebaseMap.md`.)

## The cast at a glance
| Agent | Tier → model | Runs when | Reads | Produces (typed) |
|---|---|---|---|---|
| **Planner** | cheap → Haiku | start of every run | the question (+ injected lessons) | `PlannerOutput` → question type + ordered sources |
| **Investigator** | cheap → Haiku (+ the 4 tools) | after Planner, **loops** | question, planned sources, evidence so far | `Evidence[]` (accumulated) + a `SufficiencyVerdict` per step |
| **Reasoner** | smart → Sonnet | once evidence is sufficient | question, all evidence (+ lessons) | `ReasonerOutput` → answer + root cause + confidence + trace + citations |
| **Critic** | smart → Sonnet | after the human expert answers | question, V1 answer, expert answer | `CriticOutput` → the learning event (the gap) |

Nodes never name a provider — they request a **tier** (`cheap`/`smart`) from the LLM gateway, which
maps to a model via `config/llm.yaml` (currently Claude Sonnet/Haiku, Groq fallback). All hand-offs
are **typed Pydantic** objects, threaded through one shared `GraphState`.

## The pipeline
```
START → Planner → Investigator ──(insufficient & budget left: loop / refine / broaden)──┐
                       │                                                                 │
                       └──(sufficient | max iters | sources exhausted)──→ Reasoner → END │
                                                                              ▲          │
                                                                              └──────────┘
        (after END) Human expert answer → Critic → learning event → stored → re-run improves V2
```

---

## 1. Planner  ·  *cheap tier (Haiku)*  ·  `backend/app/agents/nodes/planner.py`
**Role.** Decide *what kind* of question this is and *where to look* — the system's conditional
routing.

- **Input (from state):** `question` (and, on a re-run, injected `learning_context`).
- **Output:** `PlannerOutput { question_type, sources, rationale }` → writes
  `question_type`, `sources_to_check` (ordered), and seeds `current_query`.
- **How it works.** A cheap-tier LLM call classifies the question into a `QuestionType`
  (incident / ownership / release_delay / design_rationale / blocker / other) and picks an ordered
  subset of the four sources to investigate first.
- **Robustness.** LLM output is untrusted: the schema fields are permissive strings, then the node
  **normalizes** (`_normalize_question_type`) and filters sources to the known set; if the model
  returns nothing valid it **falls back to all sources**. A parse failure also falls back.
- **Why.** Cheap-tier is right for classification/routing (low stakes, high volume). Picking sources
  up front is the rubric's branching — and keeps the Investigator focused.
- **Viva point.** This is where a weak model can hurt **evidence coverage** (it may under-select
  sources). The Investigator's broadening (below) is the safety net.

## 2. Investigator  ·  *cheap tier (Haiku) + the 4 tools*  ·  `nodes/investigator.py` (+ `graph.py` routing)
**Role.** Gather evidence like an expert — query a source, judge whether it's enough, and keep going
or stop. **Not** a fixed top-k.

- **Each iteration:**
  1. pick the next planned source not yet queried;
  2. run its tool (`doc_search` semantic / `issue_search` / `slack_search` / `commit_search`) with the
     current query;
  3. **relevance filter** (`filter_relevant`): docs must clear a cosine floor; keyword hits need a
     positive score;
  4. accumulate + **dedup** evidence (highest score per `source_ref`);
  5. **judge sufficiency** — a cheap-tier `structured_call` returns
     `SufficiencyVerdict { sufficient, missing, refined_query }`;
  6. **broaden** — if planned sources are exhausted but it's still insufficient, add any *unsearched*
     source and keep looking.
- **Loop control** (`route_after_investigation`, a pure function): go to the Reasoner when
  `sufficient`, or `iterations >= RETRIEVAL_MAX_ITERS`, or no sources remain; otherwise loop.
- **Writes:** `evidence`, `queried_sources`, `sources_to_check` (may grow via broadening),
  `iterations`, `sufficient`, `current_query` (refined).
- **Cost/latency guardrails:** a hard **max-iterations cap**; the sufficiency prompt uses a
  **brief** evidence rendering (ids + titles, no snippets) to stay cheap.
- **Why.** Fixed top-k under-fits hard cross-source questions and over-fits easy ones; an
  adaptive loop matches how an expert investigates, and broadening recovers Planner mistakes →
  higher coverage.
- **Viva point.** Walk one trace: planned `issue+slack` → insufficient → broaden to `commit` →
  finds the revert commit → sufficient → Reasoner.

## 3. Reasoner  ·  *smart tier (Sonnet)*  ·  `nodes/reasoner.py`
**Role.** Turn evidence into the answer.

- **Input:** `question`, all accumulated `evidence` (full snippets), injected `learning_context`.
- **Output:** `ReasonerOutput { answer_text, root_cause, confidence, reasoning_trace,
  cited_source_refs }`.
- **Guardrails (the agent fails gracefully):**
  - **no relevant evidence** → short-circuits to a graceful "insufficient evidence" refusal (no LLM
    call wasted);
  - otherwise it drafts the answer, then `evaluate_answer` enforces a **confidence threshold** and
    **grounding** (cited refs must exist in the evidence) → sets `refused` + reason if it fails.
- **Why smart tier.** Synthesis + causal reasoning + calibrated confidence is the high-stakes step,
  so it gets the strongest model; cheap-tier handled the routing/sufficiency around it.
- **Viva point.** Every claim is grounded to a cited `source_ref`; low confidence or ungrounded
  citations degrade to a refusal rather than a confident hallucination.

## 4. Critic  ·  *smart tier (Sonnet)*  ·  `backend/app/learning/critic.py`
**Role.** The learning signal. It runs **outside the main graph**, when the human expert submits the
ground-truth answer.

- **Input:** the question, the AI's V1 answer (text, root cause, cited sources), and the expert's
  answer (+ root cause).
- **Output:** `CriticOutput { summary, missed_sources, missed_reasoning, corrected_root_cause }` — a
  structured **gap analysis**.
- **What happens next:** the gap becomes a **learning event** — embedded into pgvector
  (`learning/store.py`), then on a re-run the top-k relevant lessons are **injected** into the
  Planner + Reasoner prompts (`learning/injection.py`), producing a measurably better **V2**.
- **Why.** This is learning *without fine-tuning* — explainable (you can point at the exact lesson)
  and in-scope. The smart tier is used because judging "what was missed" is subtle.
- **Viva point.** Show a concrete lesson (e.g. V1 missed the revert commit / the eventual-consistency
  tradeoff) and how V2 then incorporates it.

---

## Orchestration & shared state
- **`GraphState`** (`agents/state.py`) — one Pydantic object carrying everything from question →
  answer: `question`, `learning_context`, `question_type`, `sources_to_check`, `queried_sources`,
  `evidence`, `iterations`, `sufficient`, the answer fields, and the guardrail outcome.
- **The graph** (`agents/graph.py`) — `build_graph()` wires `START → planner → investigator
  (conditional loop) → reasoner → END`; `route_after_investigation` is the (pure, testable) loop
  controller. Compiled once and reused (`get_graph`).
- **Hand-off schemas** (`agents/schemas.py`) — `PlannerOutput`, `SufficiencyVerdict`,
  `ReasonerOutput`, `CriticOutput`: typed, validated boundaries between agents.

## The supporting cast each agent leans on
- **LLM gateway** (`llm/`) — turns a *tier* into a fallback-composed model; `structured_call` gives
  provider-agnostic JSON output so every agent hand-off is validated. Models per tier come from
  `config/llm.yaml` and are shown in the UI (`GET /models`).
- **Tools** (`tools/`) — the Investigator's four senses; all return a uniform `Evidence`.
- **Learning memory** (`learning/`) — the Critic writes it; the Planner/Reasoner read it on re-run.
- **Guardrails** (`core/guardrails.py`) — relevance floor (Investigator), confidence + grounding
  (Reasoner).

## Why multi-agent (not one prompt)
Each agent has a single responsibility, a typed contract, and the *right-sized model*: cheap routing
and sufficiency checks, smart synthesis and critique. That separation is what enables conditional
routing, an adaptive retrieval loop, graceful refusal, and an explainable learning loop — none of
which a single mega-prompt gives you cleanly.
