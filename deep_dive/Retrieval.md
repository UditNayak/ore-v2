# ORE — Retrieval, explained end to end

How ORE actually *finds evidence*. This is the part that confuses people, so we go slow: the loop,
**where we use semantic search vs keyword search and why**, the **max-iteration** budget, how
documents are **ranked for relevance**, and a full **worked example**.

> TL;DR — Retrieval is **not** a single top-k call. It's an **agentic loop**: query one source →
> filter for relevance → accumulate → *ask a cheap LLM "is this enough?"* → if not, refine the query
> or broaden to another source → repeat, up to `retrieval_max_iters` (**6**). Docs are searched
> **semantically** (vector cosine); issues/Slack/commits are searched by **keyword** (term overlap).

---

## 1. The two kinds of search (and why we mix them)

ORE has **four sources**, and they are *not* searched the same way. The search method is matched to
the *shape of the data*.

| Source | Tool | Search type | Score = | Why this method |
|---|---|---|---|---|
| **Docs** (design docs, runbooks, postmortems) | `doc_search` | **Semantic** (pgvector cosine) | `1.0 − cosine_distance` | Prose is paraphrased — the answer may say "stale reads" when the question says "out-of-date data". Meaning matters more than exact words. |
| **Issues** (NIM-412 …) | `issue_search` | **Keyword** (SQL `ILIKE` + term overlap) | fraction of query terms present | Records are short, structured, and full of **identifiers** (`NIM-412`, service names, owners). Exact tokens matter; embeddings blur IDs. |
| **Slack** | `slack_search` | **Keyword** | fraction of query terms present | Same as issues — short messages, names, tokens. |
| **Commits** | `commit_search` | **Keyword** | fraction of query terms present | Commit messages are terse and identifier-heavy (`revert`, file names, SHAs). |

**Why not embed everything?** Semantic search is great for fuzzy prose but *worse* for exact tokens —
embeddings will happily rank `NIM-455` as "close" to `NIM-412` because they look alike, which is wrong.
Keyword matching is exact and cheap (no embedding call, plain SQL). So:

- **Semantic where meaning is fuzzy** → docs.
- **Keyword where tokens are exact** → issues, Slack, commits.

This split is also why their scores aren't strictly comparable (see [Ranking](#4-ranking-how-relevance-is-scored)).

---

## 2. The retrieval loop (the agentic part)

Retrieval lives in the **Investigator** node (`backend/app/agents/nodes/investigator.py`), looping
under the control of a pure routing function (`backend/app/agents/graph.py::route_after_investigation`).

```
                    ┌──────────── Planner picks ordered sources, seeds the query ───────────┐
                    │           e.g. sources_to_check = [issue, slack, commit, doc]          │
                    ▼                                                                         │
        ┌─────────────────────────── INVESTIGATOR (one iteration) ──────────────────────────┐
        │                                                                                    │
        │  1. pick next un-queried source           remaining = sources_to_check − queried   │
        │  2. run its tool(query)                    semantic (doc) OR keyword (issue/...)    │
        │  3. filter_relevant(...)                   doc: cosine ≥ 0.3   keyword: score > 0   │
        │  4. dedup_evidence(old + new)              keep highest score per (type, ref)       │
        │  5. sufficiency judge (CHEAP LLM)          SufficiencyVerdict{sufficient, missing,  │
        │                                                               refined_query}        │
        │  6. broaden (if needed)                    planned exhausted & not enough →         │
        │                                            add any un-tried source                 │
        └────────────────────────────────────────────────────────────────────────────────┬─┘
                    │                                                                       │
                    ▼   route_after_investigation(state)                                    │
        ┌───────────────────────────────────────────────────┐                             │
        │ sufficient?                  ──► yes ─────────────────────────► REASONER ──► END  │
        │ iterations ≥ MAX_ITERS (6)?  ──► yes ─────────────────────────► REASONER         │
        │ no sources left to try?      ──► yes ─────────────────────────► REASONER         │
        │ otherwise                    ──► loop back to INVESTIGATOR ──────────────────────┘
        └───────────────────────────────────────────────────┘
              (on loop, query = refined_query from the judge)
```

### What each step does

1. **Pick the next source.** `remaining = sources_to_check − queried_sources`; take the first. The
   *order* came from the Planner. If nothing remains, we're done (`sufficient = True`).
2. **Run the tool.** Dispatched by source type in `common.py::run_tool` → semantic for docs, keyword
   for the rest. Each returns a uniform `Evidence[]`.
3. **Relevance filter** (`core/guardrails.py::filter_relevant`):
   - **doc** evidence must clear the cosine floor `rag_min_score = 0.3`;
   - **keyword** evidence only needs `score > 0` (a term already matched, by construction).
4. **Accumulate + dedup** (`common.py::dedup_evidence`): merge with prior evidence, collapse repeats
   of the same `(source_type, source_ref)`, keeping the **highest** score.
5. **Sufficiency judge** — a **CHEAP-tier** `structured_call` returns
   `SufficiencyVerdict { sufficient, missing, refined_query }`. It's deliberately strict ("vague or
   tangential evidence is NOT sufficient") and is fed a **token-frugal** brief (ids + titles only, no
   snippets) to stay cheap on every loop.
6. **Broaden** — if the *planned* sources are exhausted but it's still insufficient, add any source
   not yet tried (`SEARCHABLE_SOURCES − queried`). This recovers sources the cheap Planner
   under-selected and is what pushed evidence coverage up.

### The exit conditions (loop control)

`route_after_investigation` stops the loop and goes to the Reasoner when **any** of these holds:

- `sufficient` is `True` (the judge is satisfied), **or**
- `iterations >= retrieval_max_iters` (the budget — **6**), **or**
- there are no un-queried sources left.

Otherwise it loops, and the **next iteration uses `refined_query`** suggested by the judge.

---

## 3. `max_iterations` — the budget, and why it exists

```python
# backend/app/core/config.py
retrieval_max_iters: int = 6      # hard cap on Investigator loops
rag_top_k:            int = 5      # results pulled per single search
rag_min_score:        float = 0.3 # cosine floor for a doc chunk to count
```

- **One iteration = one source queried + one sufficiency check.** With 4 sources, the loop normally
  needs ≤ 4 passes; the cap of **6** leaves headroom for **query refinement** (re-querying a source
  with a better `refined_query`) and **broadening**.
- **Why a cap at all?** Each iteration costs a cheap LLM call (and possibly an embedding). Without a
  ceiling, a hard question where the judge is never satisfied would loop forever / burn tokens. The
  cap guarantees **termination and bounded cost** — the system degrades to "answer with what we have"
  rather than hanging.
- **What happens at the cap?** We don't fail — we go to the Reasoner with whatever evidence we've
  accumulated. The Reasoner's *own* guardrails (confidence threshold + grounding) then decide whether
  to answer or refuse. So the cap controls *retrieval effort*, not *answer honesty*.

`rag_top_k = 5` is a different knob: it's how many rows a **single** search returns. The loop is what
makes total evidence adaptive — an easy question stops after one top-5 pull; a hard one gathers across
several sources.

---

## 4. Ranking — how relevance is scored

Ranking happens at **two levels**: inside each tool (rank that source's hits), then across the whole
loop (dedup keeps the best per ref).

### Within a semantic search (docs) — `doc_search.py`
```python
distance = DocumentChunk.embedding.cosine_distance(query_vec)   # pgvector, in SQL
... order_by(distance).limit(top_k)                             # closest first
score = round(1.0 - distance, 4)                                # cosine similarity, 0..1
```
- The query is embedded (`embed_query`, BAAI/bge-small, 384-dim) and pgvector orders chunks by
  **cosine distance** — DB-side, no Python loop.
- We report **similarity = 1 − distance** (higher = better). The relevance floor drops anything
  `< 0.3` so loosely-related prose never reaches the Reasoner.

### Within a keyword search (issues/Slack/commits) — `keyword.py`
```python
def keyword_score(text, query_terms):
    hits = sum(1 for t in query_terms if t in text.lower())
    return round(hits / len(query_terms), 3)   # fraction of query terms present, 0..1
```
- First **narrow** in SQL: `ILIKE %term%` OR-ed across terms/columns (`ilike_any`) so only records
  containing at least one term are pulled (over-fetched `limit*3`).
- Then **score** each by the **fraction of (stopword-stripped) query terms it contains**, sort
  descending, return top `limit`. `0.67` = two of three query terms present.

### Across the loop — `dedup_evidence`
Same `(source_type, source_ref)` can surface in multiple iterations (e.g. an issue re-found after a
query refinement). Dedup keeps the **single highest-scoring** instance, so the evidence set the
Reasoner sees is ranked, deduplicated, and floor-filtered.

> **Caveat (good viva point):** a doc `0.67` (cosine) and an issue `0.67` (term overlap) share the
> 0–1 range but mean different things. We don't globally re-rank across the two scales — each tool
> ranks its own hits, and the relevance *floor* only gates docs. The sufficiency judge, not a single
> global score, is what decides "enough."

---

## 5. Worked example

**Question:** *"Why was the NIM-412 rollout delayed, and who owned the fix?"*

**Planner** classifies this as `release_delay`, orders sources `[issue, slack, commit]`, seeds
`current_query = "NIM-412 rollout delayed owner fix"`. Stopwords (`why, was, the, and, who`) are
stripped → terms ≈ `["nim-412", "rollout", "delayed", "owner", "fix"]`.

| Iter | Source | Tool | What comes back (filtered) | Judge verdict |
|---|---|---|---|---|
| 1 | `issue` | keyword | `NIM-412` (score 0.80 — 4/5 terms) | **insufficient**, missing: *"why delayed; the actual fix"*, `refined_query: "NIM-412 rollback eventual consistency"` |
| 2 | `slack` | keyword | `t-eng-1` thread (0.50) — eng discussing the stall | **insufficient**, missing: *"the commit that fixed it"*, `refined_query: "NIM-412 revert commit"` |
| 3 | `commit` | keyword | `d4e5f6a` "revert: disable async cache for NIM-412" (0.75) | **sufficient** ✅ |

`route_after_investigation` → `sufficient` → **Reasoner**. Evidence handed over (deduped, ranked):
`d4e5f6a (0.75)`, `NIM-412 (0.80)`, `t-eng-1 (0.50)`. The Reasoner synthesizes: *delayed by an
eventual-consistency bug in the async cache; fixed by reverting it in commit `d4e5f6a`; owned by the
infra team* — every claim grounded to a cited ref.

**Broadening variant:** suppose the Planner had only picked `[issue]`. After iter 1 the planned list
is exhausted but the judge says insufficient → the Investigator **broadens**, appending the un-tried
`slack`, `commit`, `doc`, and keeps going (still under the 6-iter cap). That's the safety net for a
cheap Planner that under-selects — and why coverage stays high even when planning is imperfect.

---

## 6. Where each piece lives (quick map)

| Concern | File |
|---|---|
| The loop (one iteration) | `backend/app/agents/nodes/investigator.py` |
| Loop control / exit conditions | `backend/app/agents/graph.py::route_after_investigation` |
| Tool dispatch, dedup, evidence formatting | `backend/app/agents/nodes/common.py` |
| Semantic search (docs) | `backend/app/tools/doc_search.py` |
| Keyword search + scoring | `backend/app/tools/issue_search.py`, `slack_search.py`, `commit_search.py`, `keyword.py` |
| Query/doc embeddings | `backend/app/rag/embeddings.py` |
| Relevance floor, grounding, confidence | `backend/app/core/guardrails.py` |
| Knobs (`max_iters`, `top_k`, `min_score`) | `backend/app/core/config.py` |

See `Components.md` for the agents around retrieval, and `CodebaseMap.md` for the full file catalog.
