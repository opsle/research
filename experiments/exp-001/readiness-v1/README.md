# EXP-001 entitlement and model-identity readiness v1

Status: `PROVIDER_FREE_CONTRACT_ONLY_BLOCKED`.

This directory resolves the two provider-free readiness questions left after
the live authorization preflight. It contains no authenticated provider client,
model-generation path, authorization mutation, run creation, result creation,
or result-envelope creation.

## Account entitlement

Account entitlement means that the exact credential, organization, and project
that would execute a subject is currently permitted to invoke the exact
preregistered model through the Responses API. Public documentation, successful
authentication, billing, general organization access, public pricing, and the
ability to invoke another model are not substitutes.

OpenAI documents non-inference GET surfaces for model listing/retrieval, project
status, project API-key metadata, project model permissions, and project rate
limits. Those surfaces can bind sanitized evidence to provider-returned
organization, project, and credential IDs; negative policy can fail closed.
Current official documentation does not state that a positive response from any
one surface—or their combination—guarantees that `/v1/responses` will accept the
exact model for the exact execution credential. Therefore positive metadata is
classified `UNVERIFIED`, not `ENTITLED`.

The dormant future probe contract requires all six GET checks in
`fixtures/entitlement-unverified.json`, records only relevant fields and their
canonical SHA-256, and forbids raw responses, headers, keys, reusable
authentication, or key-derived account identities. It must run once before
authorization-set validation and again immediately before consumption; evidence
expires after 300 seconds. This repository intentionally implements validation,
not transport.

## Model identity

`gpt-5.6-sol` is the preregistered public API identifier. The official model
page's snapshot table currently repeats that same undated identifier and does
not publish a distinct immutable or dated snapshot. The Responses schema
documents a returned `model` field but no provider revision or fingerprint.
The deprecated Chat Completions `system_fingerprint` field is not a Responses
model identity and is not an immutability guarantee.

The frozen policy requires an exact provider-published immutable dated snapshot
ID, a versioned preregistration amendment naming it, direct invocation of that
ID, and exact equality with the runtime-returned `model`. Aliases and undated
identifiers without documented immutability fail closed. EXP-001 is therefore
blocked under the current public catalogue; this contract does not silently
weaken reproducibility to make the experiment runnable.

## Documentation snapshot

`documentation-snapshot.json` is a minimum-facts public documentation capture.
Its normalized facts and entire manifest are content-addressed separately. It
proves what the cited official pages stated at `2026-08-31T02:10:00Z`; it does
not prove account entitlement, future availability, immutable weights, or the
implementation served at runtime. Wholesale documentation text is not stored.

## Provider-free validation

```bash
cd experiments/exp-001/readiness-v1
python3 readiness.py \
  qualify \
  --evaluated-at \
  2026-08-31T02:10:00Z
```

The synthetic qualification result is `BLOCKED` with entitlement `UNVERIFIED`
and model identity `BLOCKED`. All six safety counters remain zero and EXP-001
remains `PLANNED`.
