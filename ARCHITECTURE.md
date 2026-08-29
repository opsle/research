# Cross-project architecture

The authoritative conceptual topology is
[`program/THEORY_MAP.md`](program/THEORY_MAP.md). The machine-readable mapping is
[`program/theory-registry.json`](program/theory-registry.json).

```text
                         PRIMARY DEVELOPER
                                |
                                v
                         FUTURE GEARBOX
                    chooses WHERE work executes
                     /          |            \
        deterministic tool  bounded helper  optional isolated worker
                     \          |            /
                                v
                        raw result/evidence
                                |
                                v
                        CONTEXT FIREWALL
                  chooses WHAT evidence returns
                                |
                                v
                     compact decision evidence
                                |
               Decision Evidence conformance
                                |
               Trajectory / Visible Value telemetry
                                |
                                v
                         PRIMARY DEVELOPER
```

Gearbox is not currently a repository or implementation. Context Firewall,
Decision Evidence Protocol, Agent Trajectory Profiler, Verifiable Agent Handoff,
and Ephemeral Agent Workers remain external, independently reusable mechanisms.

Durable orchestration is a separate family:

```text
Durable Supervisor (objective owner)
        |
        +-- Agent State Ledger (history/projection)
        +-- Agent Scheduler Runtime (readiness/time/pause)
        +-- Event-Driven Agent Wakeup (durable activation)
        +-- Agent Discovery Control (new-work admission)
        +-- Agent Recovery Policy (bounded recovery permission)
```

It can own autonomous progress across multiple activations without a
continuously active primary developer. Gearbox performs one bounded delegation
for a primary developer and returns one terminal result.

Supporting boundaries:

- Gearbox admits deterministic versus cognitive work; Routing Policy selects an
  eligible cognitive route after admission.
- Resource Claims establishes current concurrent ownership; Execution
  Authorization validates permission for one exact action.
- Scheduler decides when durable work is ready; Routing decides where it may
  run; Recovery decides whether another attempt is justified.
- Verifiable Handoff preserves exact result artifacts across source destruction;
  Context Firewall determines which verified facts enter model context.
- Semantic Edit Protocol owns mutation semantics; Agent Trajectory Profiler
  measures the resulting trajectory.

No core primitive depends on a Taslos Tasks database, worker, scheduler,
package, path, or service. Future host-specific adapters remain optional and
versioned.
