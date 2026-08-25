# Visible Value Contract

Status: normative program contract  
Receipt identity: `opsle.value-receipt.v1`

An Opsle mechanism is not product-complete when it works invisibly. When the
mechanism executes, the operator must be able to determine that it ran, what it
did, and what measurable value or protection it produced. This is an evidence
contract, not a marketing score or permission to infer benefit.

## Required surfaces

An executing mechanism normally provides all of the following:

1. a canonical machine-readable value receipt;
2. a concise, stably named operator indicator at a meaningful transition or
   completion point;
3. a durable per-run summary and compatibility with cumulative summaries;
4. explicit measurement-class, trust, aggregation, evidence, and limitation
   semantics;
5. an observational run record that can enter the production telemetry corpus
   without being mislabeled as controlled evidence.

Specifications that cannot meaningfully execute may request a narrow documented
exception. An implementation, validator, CLI, policy evaluator, or other
executable mechanism does not qualify for that exception merely because its
primary output is data.

## Receipt semantics

The canonical schema is
[`schemas/value-receipt-v1.schema.json`](schemas/value-receipt-v1.schema.json).
The executable semantic validator is `tools/validate_value_receipt.py`.

A receipt identifies the mechanism and semantic version, its exact source
revision when known, the run and operation when known, the operation name,
configuration or policy identities, measurements, evidence references, and
limitations. Unknown optional identities are `null`; they are never generated
from ambient clocks, random values, repository state, or guesses. A caller may
supply `observed_at`, but that display field is outside deterministic semantic
hashing and aggregation identity.

Each measurement states:

- its stable identity;
- baseline, result, and delta where those concepts apply;
- unit and value direction;
- measurement class;
- evidence references and source-verification state;
- whether it is operator-displayable;
- whether and how it may be aggregated;
- derivation assumptions or experimental identity when required;
- limitations.

When baseline, result, and delta are numeric, `delta = result - baseline`.
Signed deltas are valid: a packet with overhead can be larger than its raw input.
Counts and byte/token values that represent states cannot be negative. Ratios and
percentages are never directly summed.

## Measurement-quality classes

`EXACT`
: Directly and deterministically calculable from the referenced evidence. Exact
  claims require verified evidence. Examples include byte lengths, deterministic
  counts, and invariant checks.

`OBSERVED`
: Directly observed during execution without a counterfactual claim. Examples
  include an escalation, a rejection, a supplied duration, or a completed
  validation. Observed does not mean causally attributable.

`ESTIMATED`
: Derived using a named method and inspectable assumptions. Estimated token or
  monetary values remain estimates even when their byte inputs are exact.

`MODELED`
: Counterfactual or model-based inference. Predicted latency saved or predicted
  avoided turns are not facts and are not included in ordinary exact totals.

`EXPERIMENTAL`
: Supported by a controlled comparative experiment meeting the applicable Opsle
  methodology. It requires an experiment identity and controlled comparability
  evidence. Ordinary production telemetry never becomes experimental merely by
  accumulation.

## Claim ceiling and trust rules

Claims must not exceed their evidence.

- Byte evidence alone cannot claim token, monetary, latency, correctness, or
  causal savings.
- A fired safety check may report a check, rejection, inconsistency, or tamper
  signal as `EXACT` or `OBSERVED`; it may not report `failure_prevented` as a fact.
- `ESTIMATED` and `MODELED` measurements require a named method and non-empty
  assumptions. Monetary estimates require measured token input, not byte input
  alone.
- `EXPERIMENTAL` measurements require a controlled experiment identity and are
  excluded from ordinary observational aggregation.
- Only `EXACT` and `OBSERVED` numeric measurements with an explicit `SUM`
  declaration may be marked safe to aggregate. Ratios, percentages, booleans,
  states, modeled values, and experimental results are not directly summable.
- Aggregators must partition by mechanism, revision, configuration or policy,
  measurement identity, unit, class, direction, and material trust state. They
  must not add bytes to tokens, exact values to modeled values, or incompatible
  configurations.

## Operator-visible channel

The required architecture is:

```text
mechanism event
      |
      +--> decision-relevant model context
      |
      +--> operator-visible telemetry
```

Operator telemetry does not automatically become model context. For command-line
mechanisms in this program, canonical decision-relevant machine JSON is written
to stdout and one concise named indicator is written to stderr. When stdout is a
compact decision packet rather than the value receipt, a caller-requested path
may receive the canonical receipt as a deterministic sidecar. The full receipt
must not be embedded in compact model context merely for visibility. The
indicator is derived from the completed canonical result, contains no clock or
randomness, and never changes stdout. Invocation failures retain machine-readable
failure behavior and do not mix a success indicator into the error channel.

## Observational production corpus

An ordinary run record may bind the following when actually available:

- run identity, task/work classification, repository, and project;
- model and reasoning effort;
- mechanisms enabled and exact revisions/configurations;
- raw and model-visible evidence measurements;
- provider-recorded tokens;
- tool-call, child-execution, and polling-turn counts;
- passive-wait duration;
- escalation, failure, and recovery events;
- acceptance or review outcome;
- value receipts and evidence references.

Fields are optional unless a mechanism-specific profile requires them. Missing
observations remain missing rather than becoming zero. These records describe
production reality: invocation frequency, byte suppression, escalation rate,
malformed-data rejection, or visible payload. They do not establish causality.

Controlled claims such as preserved correctness, token reduction, reduced cost,
or avoided failures require a separately identified experiment with a baseline,
treatment, correctness gate, allocation method, and comparability evidence.

## Shadow and replay attachment

Future offline replay may attach, without mutating active work:

```text
completed real execution
        |
        v
freeze permissible artifacts
        |
        v
offline replay or alternate policy
        |
        v
compare under an explicit gate
```

The attachment contract records the original execution identity, replay
execution identity, baseline, treatment, content-addressed artifact identities,
and comparability status. `NOT_COMPARABLE` and missing artifacts remain explicit.
The attachment does not itself change observational evidence into causal or
experimental evidence. This contract is sufficient for later EXP-001 harness
work; no replay service is required now.

## Execution summaries

Whenever an Opsle mechanism was used, the final execution summary contains an
`Opsle Value` section. Each row names the mechanism, whether it ran, an exact or
observed result, its class, and an evidence reference when useful. Unavailable
measurements are stated as unavailable; fabricated zeroes and unmeasured savings
are prohibited.
