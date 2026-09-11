# Cross-project architecture

Opsle Tasks (`opsle/tasks`) owns current workload, task lifecycle and remote
execution. Its current default combines the control plane and local execution
inside one Incus instance, with optional SSH targets and an external exact-SHA
release broker. This research repository records evidence and program state; it has no
runtime task-management authority.

Tasks calls the versioned capability contract implemented for Task 15. Trusted
installed manifests declare hooks; operator grants bound repository selection at
the immutable task base. Capabilities supply independent public interfaces:

- Gearbox chooses deterministic or cognitive routes; model-backed capability work
  requires an execution-scoped, single-use gateway authorization.
- Context Firewall reduces command evidence, retaining canonical audit packets
  separately from semantic model evidence and actual delivery measurements.
- Affected Verification supplies verification plans and exact change capture.
  Incomplete evidence broadens verification or stops; bounded manifest-backed
  integration does not promote research beyond OBSERVE/SHADOW.
- Visible Value validates receipts and produces operator summaries without
  inventing missing values or causal savings.

Decision Evidence Protocol remains standalone because independent consumers pin
its contract. Agent Trajectory Profiler and Semantic Edit Protocol retain their
independent evidence and research boundaries. Graphify is an optional standalone
CLI, not a Tasks capability.

The final consolidation assigns ten source concepts to Tasks and Routing Policy
to Gearbox. Tasks subsequently removed its copied contract archive; exact Git
history preserves the contracts, source attribution and licenses. Current Tasks
behavior does not establish full fidelity to those historical contracts. Source
repositories are historical and cannot be active dependencies. Durable
Supervisor, Taslos Tasks and historical agent-run are retired. Paperclip remains
intentionally retained contingency infrastructure outside the research program
and backlog. Historical artifacts supply no current execution prerequisite.

Notebook implementation and production integration are complete through
[Tasks PR #83](https://github.com/opsle/tasks/pull/83), with the exact recovery,
deployment and test provenance in `program/registry.json`. Failed #51/#60 execution
history remains failed; integration does not establish research completion.
Current architecture evidence is pinned in the
[reconciliation record](program/evidence/post-consolidation/README.md).

The [generated theory map](program/THEORY_MAP.md) maps each concept and records
its current home. The [historical architecture](program/history/pre-consolidation/ARCHITECTURE.md)
preserves the earlier hypotheses without reviving their repository boundaries.
`.github` housekeeping remains separate from workload eligibility. Deployment and
release authorization remain separate from implementation and research maturity.
