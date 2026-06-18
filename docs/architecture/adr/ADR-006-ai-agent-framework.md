# ADR-006 — AI Agent Framework: Plain Python Functions

**Status**: Accepted
**Date**: 2026-06-18

---

## Context

The Veen AI pipeline has four discrete processing steps per crawl run:

1. **Filter** — remove clickbait, spam, and off-topic articles
2. **Score** — assign a 0.0–1.0 relevance score per article per topic
3. **Cluster** — group semantically similar articles covering the same event
4. **Summarize** — generate a 2–3 sentence summary per cluster

These steps have a defined sequence, pass structured data between stages, and each returns typed JSON. The question is whether to implement this as plain sequential Python functions calling the LLM API directly, or to use an agent orchestration framework.

---

## Options Considered

### Option A — Plain Python functions + direct LLM API calls (chosen)

Each step is a function that calls the OpenRouter API via the `openai` SDK, parses the JSON response, and passes the result to the next function. No framework. Full control, zero abstraction overhead.

**Pros**: Simple, no dependencies, easy to debug, no framework upgrade risk. The pipeline is a linear sequence of four steps — straightforward to implement and reason about.

**Cons**: Orchestration logic (retry on parse failure, structured output enforcement, error handling per step) must be written manually. Boilerplate grows as the pipeline gains steps.

---

### Option B — LangChain / LangGraph

General-purpose LLM orchestration framework with chains, agents, memory, and tool use. LangGraph adds graph-based workflow orchestration.

**Pros**: Large community, extensive integrations, many examples for filtering/classification pipelines.

**Cons**: Heavy dependency tree; introduces abstraction layers (runnables, chains, graphs) that add indirection without meaningful benefit for a four-step linear pipeline. LangChain's API has a history of breaking changes between minor versions.

**Rejected**: Too heavy. The pipeline is a linear sequence of four steps — not a graph, not a feedback loop, not a tool-using agent. LangChain's complexity is not justified here.

---

## Decision

Use **plain Python functions** backed by the `openai` SDK (pointed at OpenRouter). Each pipeline step is a function with a defined input type (list of articles) and output type (Pydantic model). Steps are called sequentially in `pipeline_openrouter.py`:

```
pipeline_openrouter.process(raw_articles)
├── filter_pass()    → removes clickbait, spam, low-quality articles
├── score_pass()     → scores 0.0–1.0 by topic relevance
├── cluster_pass()   → groups same-story articles
└── summarize_pass() → generates 2–3 sentence summaries
```

Structured output is enforced via OpenRouter's JSON mode and Pydantic validation at each step boundary.

---

## Consequences

### Positive

- **Zero framework overhead** — no extra dependencies, no abstraction layers to understand.
- **Easy to debug** — plain function calls with clear inputs and outputs; `logging` at each step is sufficient.
- **Pydantic schemas** — typed output validated at each step boundary catches malformed LLM responses early.
- **Single implementation** — one code path, no provider-switching logic.

### Negative / Trade-offs

- **Manual retry logic** — parse failures require manual retry handling (e.g., retry once on `ValidationError`). Acceptable for a personal project with low failure rates.
- **Boilerplate grows with pipeline steps** — adding a new step means writing the function, prompt, schema, and wiring manually. Fine at the current four-step scale.
