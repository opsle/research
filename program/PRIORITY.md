# Evidence-driven execution order

The portfolio is a dependency-aware set of parallel workstreams, not a serial
checklist.

## Workstream 1: EXP-001 prerequisites and experiment

1. Context Firewall's deterministic test-output reducer and synthetic
   conformance corpus are now prototyped at an exact revision.
2. Extend the Decision Evidence Protocol validator for packet-v1 receipts,
   suppression accounting, measurements, and explicit raw-output escalation.
3. Extend Agent Trajectory Profiler fixtures to measure visible payload, gross
   payload, escalation, and correctness-gated comparison.
4. Freeze the EXP-001 fixture set and harness, then run baseline and reduction
   arms. Add Verifiable Agent Handoff only if an arm destroys or isolates the
   source environment.

These three foundational projects are naturally tested together. The expected
first major measured experiment remains EXP-001 because no repository evidence
establishes a stronger prerequisite experiment. The experiment itself must wait
until the reducer, fixtures, correctness oracle, and exact configuration exist.

## Workstream 2: durable orchestration

Develop Agent State Ledger and the portable core of Agent Scheduler Runtime,
then test Event-Driven Agent Wakeup with Durable Supervisor. One restart,
duplicate-event, and reconstruction campaign can exercise all four mechanisms.

## Workstream 3: bounded execution and verification

Develop Agent Resource Claims and Agent Execution Authorization before combining
Ephemeral Agent Workers, Verifiable Agent Handoff, and Controlled Agent
Acceptance. This sequence makes lease/fence authority and evidence survival
testable before any real-provider acceptance is considered.

## Workstream 4: routing and recovery

Agent Routing Policy and Agent Recovery Policy should wait for durable state,
structured decision evidence, and authorization inputs. Their comparative study
can share failure fixtures and evaluate retry, alternate route, and terminal
decisions without invoking live providers initially.

## Workstream 5: editing and discovery

Semantic Edit Protocol should use Agent Trajectory Profiler for correctness-gated
payload/churn measurement and Agent Resource Claims for concurrent-region cases.
Agent Discovery Control should wait for a portable ledger and supervisor fixture
so duplicate convergence and already-satisfied proofs are durable rather than
conversation-local.

## Exact next execution

Extend the dependency-free Decision Evidence Protocol validator with Context
Firewall packet-v1 receipt, suppression, measurement, and NEEDS_RAW_EVIDENCE
conformance cases at exact revisions. Do not run a model/provider experiment in
that execution.
