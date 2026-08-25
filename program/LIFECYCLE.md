# Canonical lifecycle

The registry field `lifecycle_stage` uses exactly one of the stages below. Stages
are cumulative: promotion requires evidence for the named gate and every earlier
gate. A file's existence is not evidence that its contents satisfy a gate.

| Stage | Promotion gate |
|---|---|
| `THEORY` | A public, falsifiable problem statement identifies the proposed mechanism, scope, uncertainty, and evidence that would disconfirm it. |
| `SPECIFIED` | A versioned, normative contract defines inputs, outputs, invariants, failure behavior, compatibility boundaries, and testable conformance requirements. |
| `PROTOTYPED` | A runnable reference implementation, executable validator, or conformance suite exists at an exact revision. Automated tests exercise at least one success path and one material failure or boundary path. |
| `VERIFIED` | The scoped correctness and safety claims pass meaningful automated tests at an exact revision. Evidence records the commands, results, limitations, and failure modes. Verification of a narrow prototype does not establish comparative benefit. |
| `BENCHMARK_READY` | Immutable fixtures, a runnable harness, a real baseline, experimental arms, metrics, a correctness gate, failure classifications, and reproducible configuration are published. A prose benchmark plan is insufficient. |
| `EXPERIMENTED` | At least one measured run set has immutable identities and result artifacts. The correctness gate and failures are reported before efficiency, and the verdict is bounded to the tested conditions. |
| `REPRODUCED` | A second qualifying run set reproduces the mechanism and claimed benefit using the documented protocol in an independent environment, implementation, operator, or time window appropriate to the claim. |
| `DOCUMENTED` | Reproduction instructions, usable examples, correctness analysis, failure modes, known limitations, and relevant public/site material are complete and consistent with the evidence. |
| `COMPLETE` | Every applicable gate below is evidenced in the registry at exact revisions, no completion blocker remains, and publication material accurately states the supported domain. |

## Completion evidence

`COMPLETE` normally requires non-empty registry evidence for all of:

1. falsifiable problem statement;
2. public specification;
3. reference implementation or executable validator;
4. meaningful automated tests;
5. benchmark fixtures and runnable harness;
6. baseline comparison;
7. at least one measured experiment;
8. correctness analysis;
9. documented failure modes;
10. reproducibility instructions and a qualifying replication;
11. known limitations;
12. usable documentation and examples;
13. relevant site or publication material;
14. registry evidence tying each claim to an exact revision and artifact.

Protocols and abstractions do not need an artificial full runtime. They may meet
the implementation gate with an executable reference validator, conformance
suite, policy evaluator, or equivalent artifact. The repository's
`implementation_requirement` must state that exception and the completion
evidence must identify the executable artifact and tests. A README, theory,
interface sketch, placeholder directory, or unmeasured prototype never qualifies
by itself.

Evidence can invalidate an earlier promotion. Demotion is required when a gate is
no longer supported. Rejected or superseded work retains its highest evidenced
stage and records the disposition without rewriting history.

## Program infrastructure

Program infrastructure uses the same vocabulary with role-equivalent gates:
`THEORY` means its purpose and scope are public; `SPECIFIED` requires normative
ownership, data, update, and failure rules; `PROTOTYPED` requires working source
or tooling plus automated checks. Later gates require correctness evidence,
reproducible operations, and accurate public documentation appropriate to that
repository. Infrastructure is not `COMPLETE` merely because it renders or because
one control document exists.
