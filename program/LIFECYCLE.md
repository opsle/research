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
14. registry evidence tying each claim to an exact revision and artifact;
15. mechanism instrumentation that records whether the mechanism ran;
16. a conforming machine-readable Visible Value receipt;
17. a concise, stably named operator-visible indicator kept outside canonical
    model-visible output;
18. per-run summary integration and compatibility with durable metrics;
19. documented Visible Value claim limits, uncertainty, and measurement-quality
    semantics.

Protocols and abstractions do not need an artificial full runtime. They may meet
the implementation gate with an executable reference validator, conformance
suite, policy evaluator, or equivalent artifact. The repository's
`implementation_requirement` must state that exception and the completion
evidence must identify the executable artifact and tests. A README, theory,
interface sketch, placeholder directory, or unmeasured prototype never qualifies
by itself.

The five Visible Value gates apply to implementations, validators, CLIs, policy
evaluators, renderers, and other mechanisms that can meaningfully execute. A
narrow exception is permitted only for a specification that cannot meaningfully
execute. The completion evidence must identify each non-applicable gate, use the
exception scope `NON_EXECUTABLE_SPECIFICATION`, provide a public artifact, and
state a specific justification. Convenience, missing instrumentation, or a
documentation-first implementation is not an exception.

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

## Repository disposition and concept homes

`repository_disposition` is independent of `lifecycle_stage`: ACTIVE repositories
belong to current membership; CONSOLIDATED and RETIRED sources belong to historical
membership and cannot own active work. Retirement records SUPERSEDED completion
status and preserves the highest evidenced stage; it does not mean COMPLETE.
`consolidated_into` must name a current repository. Tasks project visibility and
`workload_eligible` do not imply research maturity; `.github` remains current but
is ineligible for workload execution.

Concept identity remains stable in the theory registry. `source_repository`
preserves origin; `current_repository` can be shared by several consolidated
concepts or null for a retired concept. `highest_evidenced_stage` preserves source
research evidence without inheriting the destination's maturity. Tasks is program
infrastructure, and Visible Value is an independently recorded concept.

Integration milestones (including remote execution and Task 15) use completed-work
records, not research COMPLETE promotions. Current and historical repository counts,
concept dispositions, homes and workload authority validate independently.

Frozen experiment participants and roles remain historical source identities.
`historical_experiment_ids` preserves reciprocal participation for retired sources
without activation. A future authorized experiment must resolve support through
the concept's current home; historical potential support is not a dependency to
revive. Experiment next-task proposals do not bypass current Tasks admission.
