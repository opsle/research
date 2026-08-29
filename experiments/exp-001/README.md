# EXP-001 offline benchmark freeze

Status: `OFFLINE_COMPONENTS_FROZEN`; EXP-001 remains `PLANNED`.

This directory freezes the provider-free portion of EXP-001, **How much context
can an AI coding agent safely not see?** It does not contain a model run, a
provider configuration, an allocated subject, or an experiment result.

## Frozen boundary

The controlled variable is the tool evidence initially made model-visible after
the same task workspace invokes the same deterministic correctness oracle:

| Arm | Initial model-visible evidence | Raw escalation |
|---|---|---|
| `raw-control` | Exact raw strict-TAP transcript | Not applicable |
| `failure-focused` | Context Firewall packet with no byte ceiling | Manual request is recorded but not fulfilled in this arm |
| `bounded-provenance` | Context Firewall packet with an 8,192-byte ceiling | Request is recorded but not fulfilled in this arm |
| `bounded-escalating` | The same bounded packet | One exact raw transcript is exposed when the packet requires escalation |

The Context Firewall packet is evidence with provenance and accounting, not an
AI summary. The current strict-TAP reducer is the only adapter under test in
this frozen revision.

The task, prompt, initial workspace, oracle, correctness gate, and raw transcript
are identical across arms. Future subject adapters must not expose oracle-only
files, accepted implementations, arm identities, or allocation mappings.

## Corpus and oracle

The corpus contains six bounded, public-safe Python standard-library repair
tasks. Each task has:

- a subject-visible prompt and initial `task.py`;
- an evaluator-only accepted implementation used solely to qualify the oracle;
- a shared evaluator-only oracle that emits the documented strict TAP subset;
- content hashes and visibility roles in `corpus/manifest.json`.

Qualification requires every initial workspace to fail at least one oracle case
and every accepted implementation to pass all cases. Oracle qualification is
not an agent or model experiment.

## Allocation and launch boundary

`allocation.json` freezes balanced-block construction and blinded label rules.
No seed, seed commitment, arm mapping, provider, model, version, reasoning
effort, sampling configuration, or repetition count is selected here. Those
items require a later preregistration and separate authorization. Until then,
no subject launch is valid and the lifecycle remains below `BENCHMARK_READY`.

## Provider-free verification

The harness fails closed unless the three pinned public Opsle dependencies are
available at their exact revisions. It executes their real implementations; it
does not reimplement their validators or call native agents.

```bash
python3 experiments/exp-001/harness.py \
  verify
```

The default dependency search checks sibling repositories and `.deps/`. Exact
paths may be supplied with `--context-firewall`, `--decision-evidence`, and
`--trajectory-profiler`.

The verification command:

1. verifies every frozen content hash and visibility boundary;
2. proves the initial/accepted oracle expectations;
3. renders every arm without a model or provider;
4. validates every Context Firewall packet against its exact source;
5. profiles every evidence trajectory with Agent Trajectory Profiler;
6. emits one canonical offline qualification report.

## Claim limits

The freeze establishes a runnable provider-free benchmark prerequisite. It does
not establish model correctness, context safety, token or cost savings, causal
benefit, a safe reduction frontier, cross-language validity, benchmark
readiness, or an experimental result. Byte measurements may be exact while all
of those broader claims remain unverified.
