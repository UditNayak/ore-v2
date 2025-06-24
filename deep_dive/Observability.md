# ORE — Observability (LangSmith + structured logs)

How to *see what the agents did* — for debugging, failure analysis, and the viva. Two layers:
**LangSmith traces** (visual, hierarchical) and **structured JSON logs** (always-on, grep-able). The
rubric's "Debugging / observability" is satisfied by either; we ship both.

> TL;DR — Set `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY` in `.env`, run a question, then open the
> **`ore`** project on smith.langchain.com. Each run is named **`ore-q{id}-v{version}`** and tagged
> **`q{id}`** / **`v{1|2}`**, so you can find the exact trace for a question and drill into every agent
> step and LLM call (latency, tokens, cost, fallbacks).

---

## 1. How it's wired (and why it "just works")

LangChain / LangGraph emit traces to LangSmith **automatically** when the right env vars are set — no
per-call instrumentation. We translate typed settings → env vars once at startup.

- **Gating** — `backend/app/core/observability.py::configure_observability()` (called from
  `app/main.py` on startup) only enables tracing when **both** `LANGSMITH_TRACING=true` **and**
  `LANGSMITH_API_KEY` are present; otherwise it logs `langsmith_disabled` and the app runs identically
  with logs only. Config lives in `app/core/config.py` (`langsmith_*`), defaulting to project `ore`.
- **Why auto-tracing captures everything** — every LLM call goes through a **LangChain Runnable**
  (`ChatLiteLLM` built in `app/llm/gateway.py`) invoked via `.ainvoke()` in `app/llm/structured.py`,
  and the whole pipeline is a **compiled LangGraph** (`app/agents/graph.py`) invoked in
  `app/services/reasoning.py`. LangSmith hooks both, so the trace shows the graph **and** its nested
  LLM calls with no extra code.
- **Per-question correlation** — the graph is invoked with a `run_name`, `tags`, and `metadata`
  (`app/services/reasoning.py`):
  ```python
  config={
      "configurable": {"session": ..., "gateway": ...},
      "run_name": f"ore-q{question.id}-v{version}",   # e.g. ore-q12-v2
      "tags": ["ore", f"q{question.id}", f"v{version}"],
      "metadata": {"question_id": question.id, "version": version},
  }
  ```
  This is what lets you *find* a trace by question in the UI (otherwise runs are anonymous).

---

## 2. Enable it

1. Get a key from smith.langchain.com → Settings → API Keys.
2. In `.env`:
   ```
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_...
   LANGSMITH_PROJECT=ore
   ```
3. `docker compose up --build`. On startup you should see the log line `langsmith_enabled project=ore`.
   (If you see `langsmith_disabled`, the key/flag isn't set.)
4. Ask a question in the UI (or run the eval). Traces appear in the `ore` project within seconds.

---

## 3. What to check on the LangSmith website

Open **smith.langchain.com → Projects → `ore`**. You'll see a list of runs.

### Find the run
- Search by **run name** `ore-q{id}-v1` (V1) or `ore-q{id}-v2` (after learning), or
- Filter by **tag** `q{id}` to see both versions of one question side by side, or by `v2` to see all
  re-runs.

### Open a run — the tree mirrors the agents
A healthy trace looks like:
```
ore-q12-v1                      (root: the LangGraph run)
├─ planner                      ← classification + source selection
│   └─ ChatLiteLLM   (cheap)    ← model, latency, prompt/completion tokens, cost
├─ investigator                 ← iteration 1
│   └─ ChatLiteLLM   (cheap)    ← the sufficiency judge
├─ investigator                 ← iteration 2 (loop! proves adaptive retrieval)
│   └─ ChatLiteLLM   (cheap)
└─ reasoner                     ← synthesis
    └─ ChatLiteLLM   (smart)    ← the expensive call
```

**What each part tells you / what to look for:**
| Look at | What it proves / debugs |
|---|---|
| **Number of `investigator` spans** | the retrieval loop actually iterated (1 per source/refinement) — your agentic loop, not a fixed top-k |
| **`planner` output** | which `question_type` + sources it chose (root-cause for low coverage = under-selection) |
| **Each `ChatLiteLLM` span** | model name (Haiku vs Sonnet — confirms cheap/smart tiering), **latency**, **prompt/completion tokens**, **cost** |
| **A retried/second model under one call** | a **fallback** fired (e.g. Groq rate-limited → Claude) — visible as two attempts |
| **`reasoner` output / low confidence** | how a **refusal** arises (confidence below threshold or ungrounded citations) |
| **Root run latency** | end-to-end time vs the <15s target |
| **Inputs/Outputs tab** | the exact prompt (incl. injected lessons on V2) and the structured JSON each agent returned |

### Compare V1 vs V2 (the learning story)
Filter by tag `q{id}`, open `ore-q{id}-v1` and `ore-q{id}-v2`:
- V2's `planner`/`reasoner` **inputs** contain the injected lesson block (`Lesson: …`, `Check
  sources: …`) — absent in V1.
- V2 typically shows **more/different investigator iterations** and a tighter answer — the visual
  proof that the learning loop changed behavior.

---

## 4. The always-on layer: structured logs

Even with LangSmith **off**, every run emits structured JSON logs (structlog), correlated by
`question_id` + `version` (bound in `app/services/reasoning.py`). The most useful events:

- `llm_call` — per call: `model`, `latency_s`, `prompt_tokens`, `completion_tokens`, `cost_usd`
  (emitted by `app/llm/metrics.py::LLMMetricsCallback`; this is also what feeds the cost/latency the
  eval reports).
- `investigated` — per loop: `source`, `new`/`total` evidence, `iteration`, `sufficient`.
- `broadened_sources`, `reasoned` (confidence/refused), `learning_injected`, `critiqued`, `learned`.

Tail them with:
```bash
docker compose logs -f backend | grep -E "llm_call|investigated|reasoned|learning_injected"
```

So: **LangSmith** for a visual, clickable trace per question; **logs** for a grep-able,
always-available record and the token/cost numbers.

---

## 5. Known limits (be honest in the viva)
- **Retrieval tools** (`doc_search`, `issue_search`, …) are plain async functions, not LangChain
  tools, so the DB queries themselves are **not** separate spans in LangSmith — you see the
  `investigator` node and its LLM call, and the retrieved evidence in the node output, but not a
  per-tool span. (The `investigated` log line covers this.)
- Tracing requires network egress to LangSmith; in fully offline/headless runs we rely on the logs.

See `Components.md` for the agents these traces visualize, and `Retrieval.md` for the loop the
`investigator` spans represent.
