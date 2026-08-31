# EXP-001 live authorization and catalogue preflight v1

Status: `PROVIDER_FREE_VALIDATION_ONLY`.

This directory implements the provider-free creation and validation of one
external four-label `LIVE_PROVIDER_RUN` authorization set and the current model
catalogue/pricing preflight for the exact preregistered `gpt-5.6-sol`
configuration.

The live authorization set is intentionally outside Git and outside every
subject context. The public evidence contains its auditable set ID and content
identity but not the block ID, subject labels, per-label authorization IDs,
allocation seed, arm mapping, raw evidence, or result envelopes.

`preflight.py create` is exclusive-create: it refuses an existing destination,
creates four unique label-bound records, marks every record `UNCONSUMED`, and
does not expose any provider transport or execution path. `preflight.py qualify`
validates without mutating the set, reproduces it twice from frozen inputs, and
executes the required fail-closed negative cases in temporary copies.

The catalogue contains only the exact preregistered candidate. Other providers
or models are not eligible without a versioned preregistration amendment. Model
availability and prices come from official OpenAI API documentation; account
entitlement remains unresolved because this task permits zero provider calls.

This preparation is not an EXP-001 run or result. It consumes no authorization,
launches no subject, creates no result envelope, advances no lifecycle state,
and makes no correctness, token, cost, latency, savings, or causal-benefit
claim.
