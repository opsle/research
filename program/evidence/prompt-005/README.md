# Prompt 005 dogfooding and interoperability evidence

This directory contains public-safe observational evidence captured while
implementing the Visible Value Contract on 2026-08-25. No model or provider
subject was run, and these artifacts are not EXP-001 evidence.

## Exact mechanism revisions

- Context Firewall: `953c48f1cfd154d6b7ed10b51b87fe54e4df45f2`
- Decision Evidence Protocol: `b17ae3b41cea7cb0b9e0befe43e885b5aa0e4a09`
- Agent Trajectory Profiler: `0a89661640721d6a39f127514b993d29bd728d47`

## Actual implementation-run observation

The raw artifact is the successful 42-test Context Firewall TAP-like Node test
output in `context-firewall-tests.tap`. Context Firewall ran on those bytes and
emitted:

```text
[Context Firewall] 3,425 B -> 13,027 B | 9,602 B expansion | escalation: yes
```

This is a useful negative observation: the strict flat TAP subset does not
classify Node's checkmark-formatted test output, so 52 of 54 source events were
ambiguous. The mechanism retained the ambiguity, expanded rather than reduced
the payload, and required raw evidence. No savings claim is made.

Decision Evidence independently re-read the source input and emitted:

```text
[Decision Evidence] source-backed packet verified | NEEDS_RAW_EVIDENCE | 7 claims checked
```

It also verified the separate Context Firewall receipt and its 11 measurements.
The Trajectory Profiler then emitted:

```text
[Trajectory Profiler] run opsle-prompt-005-dogfood | 2 receipts ingested | 11 visible measurements | 8 safe aggregates
```

The per-run summary retained 21 measurements: 10 `EXACT` and 11 `OBSERVED`.
Eight numeric measurements explicitly marked safe were aggregated without
mixing units, classes, revisions, configurations, policies, or trust states.

Three bounded implementation/inspection child executions were also directly
observed in the supervising session. That count is not included in the durable
run record because the session event stream is not exported into this public
evidence directory.

## Synthetic interoperability proof

`interoperability.json` is a deterministic public-synthetic chain over the exact
revisions above:

```text
Context Firewall receipt
        |
Decision Evidence validation receipt
        |
Agent Trajectory Profiler per-run summary
```

It proves receipt interoperability, not model correctness or causal benefit.
The large all-pass fixture measured 28,981 raw bytes and 1,846 initially visible
bytes; both receipts validated, 21 measurements were retained, and eight safe
aggregates were produced.

## Artifact roles

- `context-input.json`, `context-packet.json`, and
  `context-value-receipt.json`: reducer input, canonical model-context packet,
  and separate value sidecar.
- `context-receipt-validation.json`: independent validation of the producer
  value receipt against the packet.
- `decision-validation.json` and `decision-value-receipt.json`: independent
  packet/source result and Decision Evidence value sidecar.
- `run-record.json`, `run-record-validation.json`, and `value-summary.json`:
  ordinary observational record, validation, and deterministic per-run summary.
- `interoperability.json`: exact-revision public-synthetic conformance chain.

All timestamps and runtime-duration claims are omitted. Node's duration lines in
the raw test artifact are runner observations and are not promoted into value
receipts or causal claims.
