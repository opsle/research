# EXP-001 live authorization/provider preflight evidence

This directory records provider-free validation of one external, exact
four-label `LIVE_PROVIDER_RUN` authorization set and the current catalogue and
pricing preflight for the preregistered `gpt-5.6-sol` configuration.

The external authorization material is not committed. These public artifacts
contain only the authorization set ID and content identity, aggregate counts,
the current model catalogue, pricing derivation, validation outcomes, and the
provider-free value receipt. They omit the selected block ID, subject labels,
per-label authorization IDs, allocation seed, arm mapping, raw evidence, and
result envelopes.

Current provider facts were retrieved at `2026-08-30T18:49:10Z` from official
OpenAI documentation:

- <https://developers.openai.com/api/docs/models/gpt-5.6-sol>
- <https://developers.openai.com/api/docs/pricing>

The current direct-API standard short-context prices match the frozen EXP-001
configuration: USD 4.00 input, USD 0.40 cached input, and USD 20.00 output per
million text tokens. The official model page lists a 1,050,000-token context
window and 128,000 maximum output tokens. Account-specific entitlement and a
distinct dated snapshot remain unresolved; no provider call was made.

Qualification validates 13 authorization-set cases, including two
byte-identical deterministic replays and the required fail-closed negative
cases. It records four live labels, zero subject renderings, zero subject-visible
canonical arm identifiers, zero provider/model launches, zero authorization
consumptions, zero result envelopes, and zero experiment runs/results.

EXP-001 remains `PLANNED`. This evidence does not establish model correctness,
token or cost savings, latency savings, comparative performance, or causal
benefit.
