# ADR-003 — AI Gateway: OpenRouter

**Status**: Accepted
**Date**: 2026-06-18

---

## Context

The Veen AI pipeline calls a large language model for four tasks per crawl run: filtering clickbait/off-topic articles, scoring articles by relevance, clustering similar stories, and generating cluster summaries. The best model for each task is not fixed — the AI landscape changes rapidly and cost/quality trade-offs shift frequently.

The pipeline needs a gateway that allows model swaps without code changes, provides an OpenAI-compatible interface, and keeps operational overhead low.

---

## Options Considered

### Option A — OpenRouter (chosen)

Model-agnostic HTTP gateway routing to 100+ models (Claude, GPT-4o, DeepSeek, Mistral, etc.). All LLM calls use the `openai` Python SDK with `base_url` set to the OpenRouter endpoint. Model is specified per-request via the `model` parameter; swapping models is a one-line env var change (`VEEN_AI_MODEL`).

**Cost**: ~$0.01–0.10 per daily run depending on model chosen (DeepSeek v4 Flash: ~$0.14/1M tokens).

**Pros**: Model-agnostic — no vendor lock-in; one API key manages all providers; OpenAI SDK is battle-tested with async, retries, and structured outputs.

**Cons**: Pay-per-use — not free. External dependency on openrouter.ai availability.

---

### Option B — Direct Anthropic SDK

**Pros**: Official support, lowest latency to Claude models, direct billing relationship.

**Cons**: Locks the codebase to Claude. Switching to any other model requires installing a different SDK, rewriting message formatting, and updating error handling across all pipeline stages.

**Rejected**: Model-agnostic access via OpenRouter provides Claude model access without the lock-in.

---

### Option C — Ollama (local inference)

**Pros**: Truly zero AI cost — models run locally on developer hardware.

**Cons**: Requires a GPU for practical inference speeds. Running on CPU for 200 articles would take 30–60 minutes — too slow for a daily crawl targeting < 10 minutes total. Model quality at the 7B–13B range is noticeably lower than cloud models for classification and summarization.

**Rejected**: OpenRouter achieves acceptable cost at cloud inference quality without the hardware dependency.

---

## Decision

Use **OpenRouter** as the single AI gateway. All LLM calls use the `openai` Python SDK pointed at `https://openrouter.ai/api/v1`. The active model is controlled by the `VEEN_AI_MODEL` GitHub Actions variable — changing the model requires updating one variable in the GitHub Actions UI with no code change or redeploy.

---

## Consequences

### Positive

- **Model-agnostic** — swap to any OpenRouter-supported model by changing one env var.
- **OpenAI SDK** — battle-tested, well-documented, async-native, handles retries and structured output.
- **Low cost** — cheap models (DeepSeek Flash) keep daily crawl cost negligible.
- **Single code path** — no provider-switching logic, no fallback branches to maintain.

### Negative / Trade-offs

- **Pay-per-use** — not free; cost scales with usage. Negligible for a personal daily crawl but worth monitoring.
- **External dependency** — openrouter.ai availability affects the pipeline. Mitigated by OpenRouter's SLA and the low-criticality nature of a personal news digest.
