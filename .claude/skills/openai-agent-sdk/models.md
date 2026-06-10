# Models and pricing

Contents:
- OpenAI text models
- OpenAI embedding models
- Gemini models
- Choosing a model

All prices are USD per 1M tokens (Standard tier, paid). Batch tiers are roughly 50% off. Set the slug as the agent `model`.

## OpenAI text models

| Slug | Input | Cached input | Output |
|------|-------|--------------|--------|
| `gpt-5.5` | 5.00 | 0.50 | 30.00 |
| `gpt-5.4` | 2.50 | 0.25 | 15.00 |
| `gpt-5.4-mini` | 0.75 | 0.075 | 4.50 |
| `gpt-5.4-nano` | 0.20 | 0.02 | 1.25 |

`gpt-5.5` is the flagship for complex reasoning and coding (pricing applies under 272K context). Drop to `gpt-5.4-mini` or `gpt-5.4-nano` when latency and cost matter more than peak quality. All support text and image input, text output, and vision via the Responses API.

## OpenAI embedding models

| Slug | Price |
|------|-------|
| `text-embedding-3-small` | 0.02 |
| `text-embedding-3-large` | 0.13 |
| `text-embedding-ada-002` | 0.10 |

Default to `text-embedding-3-small`; use `text-embedding-3-large` when retrieval quality justifies the cost.

## Gemini models

Use via the Gemini API. Output prices include thinking tokens. Context-cache storage is billed separately (~$1.00 / 1M tokens per hour).

| Slug | Input | Output | Cache (read) |
|------|-------|--------|--------------|
| `gemini-3.5-flash` | 1.50 | 9.00 | 0.15 |
| `gemini-3.1-flash-lite` | 0.25 (text/image/video), 0.50 (audio) | 1.50 | 0.025 |
| `gemini-3.1-pro-preview` | 2.00 (≤200K), 4.00 (>200K) | 12.00 (≤200K), 18.00 (>200K) | 0.20 / 0.40 |

- `gemini-3.5-flash` — most intelligent built for speed, with strong search and grounding.
- `gemini-3.1-flash-lite` — most cost-efficient, for high-volume agentic tasks, translation, and simple data processing.
- `gemini-3.1-pro-preview` — top multimodal, agentic, and coding quality (preview; rate limits and pricing may change).

Grounding with Google Search/Maps: 5,000 prompts/month free (shared across Gemini 3), then $14 / 1,000 queries.

## Choosing a model

| Need | Pick |
|------|------|
| Complex reasoning, coding, default | `gpt-5.5` or `gemini-3.1-pro-preview` |
| Balanced cost/quality | `gpt-5.4` or `gemini-3.5-flash` |
| High-volume, latency-sensitive | `gpt-5.4-mini`, `gpt-5.4-nano`, or `gemini-3.1-flash-lite` |
| Embeddings / retrieval | `text-embedding-3-small` (default), `text-embedding-3-large` (quality) |
