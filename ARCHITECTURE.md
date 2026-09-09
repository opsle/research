# Cross-project architecture

Opsle Tasks (`opsle/tasks`) owns current workload, task lifecycle and remote
execution. Its control plane and Incus execution targets are independently
deployed. This research repository records evidence and program state; it has no
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

The final consolidation places ten source concepts under Tasks contracts and
Routing Policy under Gearbox. Source repositories are historical and cannot be
active dependencies. Durable Supervisor, Taslos Tasks, Paperclip and historical
agent-run are retired. Findings, source attribution, licenses and experiment
artifacts remain evidence; none supplies a current execution prerequisite.

The [generated theory map](program/THEORY_MAP.md) maps each concept and records
its current home. The [historical architecture](program/history/pre-consolidation/ARCHITECTURE.md)
preserves the earlier hypotheses without reviving their repository boundaries.
`.github` housekeeping remains separate from workload eligibility. Deployment and
release authorization remain separate from implementation and research maturity.
