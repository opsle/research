# Canonical Opsle theory map

Status: authoritative conceptual reconciliation plus the 2026-08-29 public
Gearbox extraction and 2026-08-31 Affected Verification project creation.
Consolidation and disposition operations remain recommendations only.

Machine source: [`theory-registry.json`](theory-registry.json).

Theory registry canonical SHA-256:
`7cdc866ada723f24fd16af005bb54b9a60873e0623effb70df691a7a58fcdc47`.

This map corrects an extraction-boundary error. The original 16 concept
repositories were useful hypotheses isolated from one production system, but
hypothesis granularity was treated as repository and product granularity. The
resulting cross-repository diagram then placed almost every concept in one autonomous
supervisor pipeline. Agent Gearbox initially had no canonical home, and shared words such
as *bounded child*, *delegation*, and *waiting without inference* allowed its
primary-developer transmission theory to be conflated with Durable Supervisor.

The separately authorized Gearbox extraction created one public repository and
assigned its new, evidence-backed implementation `PROTOTYPED`. No existing
repository was promoted, demoted, consolidated, renamed, archived, or deleted.
Existing evidence remains attached to the exact implementation or profile it
actually exercises.

## Canonical topology

```text
OPSLE
├── Agent Gearbox                          public narrow prototype
│   ├── deterministic-versus-cognitive admission
│   ├── gear and model/effort selection
│   ├── content-addressed bounded context
│   ├── deterministic executor / bounded helper executor
│   ├── OS/transport passive wait
│   ├── compact result, literal budget, cleanup, and value telemetry
│   └── consumes external policies/protocols where required
├── Independent Opsle tools
│   ├── Context Firewall
│   ├── Agent Trajectory Profiler
│   ├── Affected Verification
│   └── Semantic Edit Protocol
├── Cross-cutting protocols
│   ├── Decision Evidence Protocol
│   └── Verifiable Agent Handoff
├── Gearbox-facing supporting policy research
│   ├── Agent Routing Policy
│   ├── Agent Execution Authorization
│   └── Agent Resource Claims
├── Durable orchestration research family
│   ├── Durable Supervisor                 family hypothesis / objective owner
│   ├── Agent State Ledger                 history and projection module
│   ├── Agent Scheduler Runtime            readiness and time module
│   ├── Event-Driven Agent Wakeup           durable activation module
│   ├── Agent Discovery Control             discovered-work admission module
│   └── Agent Recovery Policy               bounded recovery permission module
├── Execution and isolation infrastructure
│   └── Ephemeral Agent Workers
└── Research-only system acceptance
    └── Controlled Agent Acceptance
```

The tree is conceptual, not a repository-creation plan. In particular, the
Durable Supervisor family has multiple recorded repositories today but likely
fewer future implementation boundaries. Conversely, Context Firewall, Decision
Evidence, Profiler, Semantic Edit, Handoff, and isolation have meaningful reuse
outside either Gearbox or durable orchestration.

## Agent Gearbox

> Agent Gearbox lets a powerful primary developer delegate routine operations
> and bounded work to deterministic software or less expensive models, then
> receive only the compact result needed to continue.

Guiding idea: **Stop using intelligence for work that does not require
intelligence.**

The primary developer retains end-to-end project understanding, architecture,
safety decisions, integration, ambiguity resolution, and the final definition
of completion. Gearbox is subordinate to that developer and one explicit
bounded call resembling:

```text
gearbox_run(
  task,
  task_type,
  requested_gear,
  allowed_context,
  output_contract,
  authority,
  budget
)
```

### Irreducible mechanism

1. Validate the task, authority, context manifest, requested gear, model and
   effort limits, output contract, and literal budget.
2. Admit deterministic software whenever cognition is unnecessary.
3. Admit one fresh bounded helper only when cognition is necessary.
4. Resolve only explicitly allowed, content-addressed context.
5. Execute through a deterministic or bounded cognitive gear.
6. Block at the OS or transport layer until the bounded execution terminates;
   the primary model does not poll.
7. Keep raw logs outside primary model context and addressable.
8. Return one compact structured success, failure, indeterminate, or escalation
   result.
9. Terminate temporary helpers, reconcile residue, and fail closed if bounded
   cleanup cannot be established.
10. Emit exact or observed Visible Value telemetry without inventing token,
    cost, latency, or causal savings.

### Current minimal package boundary

```text
src/
├── contract/        request, result, gear, budget, and error schemas
├── admission/       deterministic-vs-cognitive and requested-gear validation
├── context/         content-addressed allow-manifest resolution
├── gears/
│   ├── deterministic/
│   └── bounded-helper/
├── transport/       passive blocking and terminal-result capture
├── budget/          literal provider/session/tool/time accounting
├── cleanup/         helper termination and residue reconciliation
├── result/          compact result assembly and fail-closed escalation
└── telemetry/       Visible Value and trajectory emission hooks
```

The public reference core currently implements these responsibilities in a
small Python package rather than one module per diagram node. The diagram is a
responsibility map, not a requirement to split packages or repositories.

### External dependencies and profiles

- **Context Firewall** adapts raw tool or helper evidence for primary context.
  Gearbox does not own reducer policies.
- **Decision Evidence Protocol** defines or validates compact result facts.
  Gearbox owns execution, not general evidence-protocol governance.
- **Agent Trajectory Profiler** consumes execution and Visible Value telemetry.
  It never selects a gear.
- **Agent Routing Policy** may supply one Gearbox-specific model, effort, and
  provider route after Gearbox admits cognitive execution.
- **Agent Execution Authorization** may validate a capability-style authority
  envelope. Reduction and redaction never become authorization.
- **Agent Resource Claims** is optional when shared mutable resources require
  leases and fences; it is not needed for every bounded call.
- **Ephemeral Agent Workers** is optional execution/isolation infrastructure for
  risky helpers; deterministic local gears need not use it.
- **Verifiable Agent Handoff** is optional when a helper source environment will
  be destroyed before independent verification.

### Explicit non-responsibilities

Gearbox must not absorb:

- durable objective ownership, cross-activation reconstruction, queues,
  schedules, Global Pause, or autonomous discovery;
- autonomous retry, consultation, alternate-provider fallback, or recovery;
- a persistent hierarchy of agents or a second permanent supervisor;
- exact-session resume or replacement of ChatGPT Remote;
- generic worker isolation, handoff storage, or every Opsle protocol;
- final integration or completion authority from the primary developer.

### Visible Value contract

A Gearbox run should expose, when directly observed:

- requested, admitted, and executed gear;
- deterministic operation identity or helper model/effort identity;
- content manifest identity and permitted bytes/artifacts;
- provider sessions actually started, with missing counts left missing;
- passive-wait duration only when directly measured outside deterministic
  semantic output;
- helper termination and residue state;
- raw and returned evidence bytes from compatible Context Firewall receipts;
- exact budget use and typed rejection/escalation reasons.

It may report a deterministic task completed with zero provider sessions when
that fact is directly recorded. It may not call that value *tokens saved* or
*cost avoided* without a controlled baseline and provider-recorded usage.

## Gearbox versus Durable Supervisor

| Dimension | Agent Gearbox | Durable Supervisor / autonomous orchestration |
|---|---|---|
| Primary owner | One continuously responsible powerful primary developer | A durable objective-owning supervisor or orchestrator |
| Persistence | Bounded call state; durable receipts/artifacts as needed | Durable objective, work, event, attempt, and reconstruction state |
| Session lifecycle | One primary-developer activation delegates and receives one terminal result | May stop and resume reasoning across multiple activations |
| Child purpose | Perform one routine operation or bounded cognitive assignment cheaply | Advance autonomous objective state between supervisor decisions |
| Waiting | Synchronous OS/transport blocking without primary-model polling | Persisted wait registration and event-driven reactivation |
| State | Content manifest, request, result, budget, and cleanup state for one call | Ledger projection spanning objectives, tasks, attempts, schedules, and events |
| Retry/recovery | None by default; return failure or indeterminate and fail closed | May use a separately authorized bounded recovery policy across attempts |
| Scheduling | None beyond executing the current bounded call | Queues, dependencies, timeouts, schedules, pause, and readiness transitions |
| Completion | Returns a compact result; the primary developer decides project completion | Records durable task/objective transitions under evidence gates |
| Context ownership | Primary developer owns project context; Gearbox sees only an allowlisted slice | Supervisor reconstructs the model-readable state required for the next activation |
| Intended use | Save the primary developer's intelligence and context on routine bounded work | Operate long-horizon autonomous work despite inactive or interrupted reasoning sessions |
| Failure model | One typed terminal result, escalation, literal budget, helper termination, no hidden fallback | Crash/restart, duplicate/lost events, stale projections, retries, recovery, and terminal orchestration states |

Canonical invariant:

> Gearbox enhances a primary developer. Durable orchestration owns progress
> across activations without requiring that developer to remain continuously
> active.

The earlier wording “can operate across multiple activations” is necessary but
not sufficient. The decisive distinction is **objective ownership**: Gearbox
never takes the primary developer's end-to-end ownership, whereas a Durable
Supervisor owns durable autonomous progress between decisions.

The prior drift occurred because Durable Supervisor and Event Wakeup also use a
fresh child, bounded assignment, and no model inference while waiting. Their
durable objective, reconstruction, scheduler, and reactivation semantics are the
parts that make them a different theory.

## Context Firewall

> Context Firewall is a deterministic boundary that keeps operational noise out
> of an AI agent's context while preserving the compact evidence, provenance,
> and escalation path the agent needs to make correct decisions.

```text
tool or process
      ↓
raw addressable evidence
      ↓
deterministic versioned adapter and policy
      ↓
compact evidence packet
      ↓
model context
```

The packet carries the functional equivalent of schema/policy version,
producer/tool class, source identity and SHA-256, exit state, compact facts,
retained/suppressed accounting, completeness, raw locator, escalation state and
reason, and a deterministic packet identity.

Context Firewall is not an AI summarizer, sandbox, authorization system,
redaction system, evidence deletion mechanism, supervisor, or proof that model
correctness was preserved. It fails closed or escalates for unsupported formats,
incomplete parsing, uncertain identity, unexpected truncation, unsafe evidence
ceilings, unclassifiable evidence, missing or hash-invalid raw artifacts, and
source/policy incompatibility.

The current repository implements one strict flat TAP-compatible adapter. That
adapter supports `PROTOTYPED` for its scoped implementation; it does not imply
the adapter families below exist.

### Intended adapter families

| Family | Likely compact facts | Unsafe to hide | Escalation conditions | Raw artifact handling |
|---|---|---|---|---|
| Tests | runner/profile, exit/interruption, pass/fail/skip totals, failed identities and complete failure regions, duration when supplied | every failure, crash, timeout, contradiction, flaky/retry marker that changes verdict | unsupported dialect, nested structure not understood, truncated failure, contradictory counts, unexplained exit, ceiling cannot retain failures | retain exact stdout/stderr bytes, framed hash, runner identity, and immutable locator |
| Lint | tool/config/version, file/rule/severity counts, affected paths, fixability, exit state | errors, parser/config failures, suppressed-rule changes, unsafe autofix warnings | unknown formatter, omitted diagnostics, path ambiguity, config mismatch, truncated output | retain complete diagnostics and config identity; packet links line/rule facts to raw bytes |
| Typecheck | compiler/project version, diagnostic codes, files/locations, error counts, build mode | all type errors, project-reference failures, emit-on-error behavior, config resolution defects | unrecognized diagnostic grammar, incremental cache uncertainty, truncated chains, project/config drift | retain compiler streams, project graph/config hashes, and artifact locator |
| Git | repository/worktree identity, HEAD/base/target, status counts, changed paths, diff/stat/ref outcomes | conflicts, unmerged entries, rejected refs, dirty-overlap evidence, signature or object failures, destructive target ambiguity | ambiguous repository, stale refs, truncated diff, unsafe path encoding, missing objects, hash mismatch | retain exact command output and required diff/bundle/object evidence with repository identity |
| Build/compiler | toolchain/config/target, exit state, produced artifact identities, error/warning counts, cache state | compile/link errors, missing outputs, nondeterminism warnings, unsafe fallback, signing or packaging defects | unsupported formatter, missing artifact, cache provenance uncertain, truncated diagnostic, artifact hash mismatch | retain logs plus content-addressed outputs, manifests, and toolchain/config identity |
| Processes/services | command/unit identity, exit/signal, health state, revision, bounded recent error facts | crash loops, unhealthy identity/revision, permission failures, timeouts, resource exhaustion, cleanup residue | uncertain process identity, log gap, unexpected truncation, health/workload disagreement, missing start/end evidence | retain bounded journal/process artifacts with cursor/time window, command/revision identity, and hashes |
| Helper-agent results | task/context/authority/budget/model identity, terminal status, changed artifacts, verification, limitations, cleanup | any failure, uncertainty, unauthorized access, budget breach, incomplete verification, residue, hidden retry/fallback | malformed result contract, context mismatch, missing raw transcript/artifact, provider identity uncertainty, truncated result, helper not terminated | retain raw transcript/logs outside primary context, content-addressed result artifacts, request/response hashes, and cleanup receipt |

## Seventeen repository classifications

The classification is conceptual. The disposition is a future recommendation,
not an executed repository action.

| Repository | Primary classification | Recommended disposition | Confidence | One-sentence rationale |
|---|---|---|---|---|
| `gearbox` | `GEARBOX_CORE` | `KEEP_STANDALONE` | `HIGH` | One bounded primary-developer transmission operation now has a narrow public home without absorbing durable orchestration or external policies and protocols. |
| `affected-verification` | `INDEPENDENT_OPSLE_TOOL` | `KEEP_STANDALONE` | `HIGH` | Minimum-defensible verification planning composes native impact evidence, catalogs, and risk policy without owning check execution or model-context reduction. |
| `agent-trajectory-profiler` | `INDEPENDENT_OPSLE_TOOL` | `KEEP_STANDALONE` | `HIGH` | Reusable correctness-gated telemetry is external to both Gearbox and durable orchestration, although generic Visible Value scope needs ownership cleanup. |
| `semantic-edit-protocol` | `INDEPENDENT_OPSLE_TOOL` | `KEEP_STANDALONE` | `HIGH` | Bounded structural editing is independently useful and can be selected as a deterministic Gearbox tool without becoming Gearbox core. |
| `durable-supervisor` | `DURABLE_ORCHESTRATION` | `KEEP_AS_RESEARCH` | `HIGH` | Durable objective ownership and reconstruction form a distinct autonomous-orchestration hypothesis whose package boundary remains unproven. |
| `event-driven-agent-wakeup` | `DURABLE_ORCHESTRATION` | `CONSOLIDATE_WITH_OTHER` | `MEDIUM_HIGH` | Durable wait registration and event reactivation share the supervisor/scheduler state boundary and are not Gearbox's synchronous passive wait. |
| `context-firewall` | `INDEPENDENT_OPSLE_TOOL` | `KEEP_STANDALONE` | `HIGH` | Deterministic evidence adaptation has standalone value; the current TAP reducer is one adapter, not the whole concept. |
| `decision-evidence-protocol` | `CROSS_CUTTING_PROTOCOL` | `KEEP_AS_PROTOCOL` | `HIGH` | Vendor-neutral evidence representation and independent conformance are reused by many producers and consumers. |
| `agent-state-ledger` | `DURABLE_ORCHESTRATION` | `CONSOLIDATE_WITH_OTHER` | `MEDIUM_HIGH` | The ledger is the Durable Supervisor family's authoritative history/projection module rather than a second product boundary. |
| `agent-scheduler-runtime` | `DURABLE_ORCHESTRATION` | `CONSOLIDATE_WITH_OTHER` | `HIGH` | Readiness, time, pause, and queue transitions belong to the durable-orchestration runtime and currently overlap claims, routing, and recovery. |
| `verifiable-agent-handoff` | `CROSS_CUTTING_PROTOCOL` | `KEEP_AS_PROTOCOL` | `HIGH` | Durable result transfer across source destruction is reusable, while the current HMAC code proves only a seal subcomponent. |
| `agent-routing-policy` | `GEARBOX_SUPPORTING_POLICY` | `FUTURE_GEARBOX_POLICY` | `MEDIUM_HIGH` | Gearbox needs a scoped model/effort/provider route policy after gear admission, but reviewer and fallback routing remain external concerns. |
| `agent-resource-claims` | `GEARBOX_SUPPORTING_POLICY` | `KEEP_AS_RESEARCH` | `MEDIUM` | Leases and fencing can support Gearbox and other systems, but a portable policy boundary and independent packaging value are not yet proven. |
| `agent-discovery-control` | `DURABLE_ORCHESTRATION` | `CONSOLIDATE_WITH_OTHER` | `HIGH` | Autonomous discovered-work admission depends on the supervisor's durable objective graph, ledger, and budgets and is outside explicit-task Gearbox. |
| `agent-execution-authorization` | `GEARBOX_SUPPORTING_POLICY` | `FUTURE_GEARBOX_POLICY` | `HIGH` | Exact capability-style authority is required before Gearbox execution but remains reusable by orchestrators and isolation infrastructure. |
| `controlled-agent-acceptance` | `RESEARCH_ONLY_HYPOTHESIS` | `KEEP_AS_RESEARCH` | `MEDIUM_HIGH` | One-shot autonomy acceptance is an experiment-control method, not a production runtime or Gearbox component. |
| `agent-recovery-policy` | `DURABLE_ORCHESTRATION` | `CONSOLIDATE_WITH_OTHER` | `HIGH` | Recovery permission relies on durable attempts and shared budgets; canonical Gearbox explicitly performs no autonomous retry or fallback. |
| `ephemeral-agent-workers` | `EXECUTION_ISOLATION_INFRASTRUCTURE` | `KEEP_STANDALONE` | `HIGH` | Brokered disposable execution and destruction proof are reusable infrastructure independent of reasoning and orchestration. |

Detailed original problems, implementation fidelity, drift status, gains, risks,
provenance concerns, relationships, dependencies, consumers, evidence, and
unresolved questions are machine-readable in `theory-registry.json`.

## Accidental duplication and exact boundaries

### Gearbox selection versus routing

Gearbox decides whether the explicit task should use deterministic software or
bounded cognition and validates the requested gear. Routing selects one eligible
model/provider/profile after cognitive admission. Routing does not admit
cognition and neither decision authorizes autonomous fallback.

### Discovery versus routing

Discovery decides whether newly proposed autonomous work should exist. Routing
decides where an already admitted cognitive attempt may run. Gearbox accepts an
explicit primary-developer task and creates no recursive work.

### Authorization versus resource claims

Resource Claims establishes current ownership of a conflicting resource set
through leases and fences. Execution Authorization decides whether a subject may
perform one exact action and binds current claim identity plus immutable source,
target, purpose, and route authority. Authorization references claims; it does
not reimplement claim lifecycle.

### Scheduler versus resource claims and routing

Scheduler owns **when** durable work is ready. Claims owns **who currently
controls** a resource. Routing owns **where/by which eligible executor** a
cognitive attempt may run. Provider availability is route evidence; retry timing
is scheduler/recovery state.

### Recovery versus routing and acceptance

Recovery decides whether another attempt can add information or change
conditions and which recovery class is allowed. Routing selects the exact route
only for that separately authorized attempt. Controlled Acceptance preserves
first-failure behavior and cannot silently enable recovery unless its immutable
manifest says so.

### State Ledger versus Durable Supervisor

The ledger records immutable facts and projects current state. Durable
Supervisor owns objective decisions based on that projection. No supervisor,
scheduler, or discovery module may maintain a competing authoritative history.

### Event wakeup versus scheduler

The scheduler owns wait readiness and timeout policy; the wakeup module persists
registrations and delivers idempotent decision-relevant activation events. One
shared event identity and store contract is required.

### Handoff versus Decision Evidence and workers

Decision Evidence owns generic fact/receipt conformance. Handoff adds exact
artifact identity, durable-before-destroy ordering, and fresh reconstruction.
Worker infrastructure enforces containment and lifecycle, then consumes Handoff
for result transfer. A worker must not mint its own authorization or duplicate
the handoff protocol.

### Context Firewall versus Decision Evidence and Profiler

Context Firewall reduces and emits. Decision Evidence validates the packet and
its claims independently. Profiler records exposure and value observations. The
Decision Evidence validator may reclassify source bytes for a pinned conformance
profile, but it must not evolve into a competing reduction policy. Profiler must
not become the normative owner of every receipt protocol merely because it
aggregates them.

### Affected Verification versus selectors, Gearbox, and Context Firewall

Native affected/related systems remain authoritative evidence providers for
their own graphs and test frameworks. Affected Verification composes that
evidence with a complete verification catalog and explicit risk policy to
produce selected checks, explained skips, and a sufficiency or uncertainty
state. It does not reimplement those selectors, execute CI, or claim global
mathematical minimality.

Gearbox may consume a plan and choose an execution gear, but does not own the
verification theory or planner. After checks execute, Context Firewall decides
which results enter model context; Affected Verification decides only what
verification should execute. Decision Evidence may validate plan provenance,
and Agent Trajectory Profiler may measure planned versus actual or shadow work,
without initial package coupling.

## Restored home and remaining gaps

`opsle/gearbox` now coherently owns deterministic task admission, requested-gear
validation before model/provider routing, content-addressed staged helper
context, exact model and reasoning-effort profiles, one injected bounded helper
transport, OS-level blocking wait, compact result and failure contracts,
literal command/provider/context/output/time budgets, termination checks, raw
artifact accounting, and directly observed provider-session counts.

The portable core deliberately leaves production helper isolation, provider
routing, general execution authorization, Context Firewall adapters, Decision
Evidence conformance, and trajectory aggregation outside its ownership. A
production helper transport and controlled provider-session/correctness/context
comparison remain implementation and evidence gaps. No concept now lacks a
machine-recorded home, and these responsibilities do not justify additional
repositories.

## Implementation fidelity and lifecycle scope

- Agent Gearbox is prototyped for its provider-free public core: deterministic
  execution and injected-helper contract paths are runnable and tested, while
  no production helper transport, Context Firewall integration, comparative
  benchmark, or model/provider subject exists.
- Agent Trajectory Profiler is verified for its implemented metrics, Context
  Firewall profile, run records, and Visible Value summaries; predictive or
  causal benefit remains unmeasured.
- Context Firewall is prototyped for the TAP-subset adapter. No other adapter
  family exists, and no safe correctness frontier is known.
- Decision Evidence is verified for the Context Firewall and Visible Value
  profiles. Its generic multi-tool envelope remains narrow.
- Event-Driven Agent Wakeup is prototyped only as an in-memory transition
  function; durability, restart, event delivery, and timeout behavior are not
  implemented.
- Verifiable Agent Handoff is prototyped only for HMAC manifest binding and
  caller-supplied destruction state; publication, transport, destruction proof,
  reconstruction, and independent verification are not implemented.
- Affected Verification is verified for its narrow deterministic planner and
  the revision-bound AV-EXP-001 Zustand/Vitest shadow calibration. Its frozen
  corpus observed 8/8 relevant checks selected by both AV arms, including
  conservative full broadening under incomplete impact evidence. The result is
  still one repository, one ecosystem, and mostly synthetic change/fault
  shapes; no production adapter, independent qualifying replication, or trusted
  selective-verification class exists.
- The remaining theory repositories contain coherent falsifiable narratives,
  but their `SPEC.md` files are generic templates and their source/tests are
  placeholders. Their current lifecycle remains `THEORY`.

Conceptual reclassification neither promotes nor demotes any repository. A
future consolidation does not combine lifecycle stages arithmetically: evidence
continues to support only its exact historical concept, revision, and scope.

## EXP-001 reconciliation

`EXP-001` remains the correct first controlled Context Firewall experiment:

> How much context can an AI coding agent safely not see?

Three layers must remain separate:

1. **Concept definition:** deterministic evidence boundary with provenance,
   completeness, raw addressability, and fail-closed escalation.
2. **Current prototype:** one strict TAP-subset adapter and its packet/value
   contracts.
3. **Experimental hypothesis:** reduced context preserves task correctness under
   equal fixtures, models, prompts, and correctness gates.

The conformance corpora and Prompt 005 dogfood evidence validate implementation
behavior; they are not an EXP-001 result. The content-addressed task corpus,
correctness oracle, baseline and arms, offline harness, exact model/provider
configuration, blinded allocation, coordinator, and provider-free live
preflight are frozen or qualified at their recorded revisions. `EXP-001` stays
`PLANNED` with zero run identities and zero result artifacts.

EXP-001 has no technical dependency on Gearbox, and no provider/model subject is
authorized by the provider-free preparation. Controlled experiments are now
LATER program work rather than the immediate execution; the authoritative
current priority is the machine state in `program/registry.json`.

## Public Opsle and Taslos Tasks boundary

The 2026-08-25 extraction snapshot is historical provenance, not a dependency
direction. Taslos Tasks remains private/active and unchanged. Production
complexity demonstrated that several mechanisms were possible, but does not
establish their general primitives, repository boundaries, or comparative
benefit.

The long-term direction is:

```text
public Opsle mechanisms and protocols
                ↓
future public Opsle Tasks and other products consume pinned versions/adapters
```

It is not:

```text
private Taslos Tasks remains the canonical implementation
                ↓
public concepts are repeatedly rediscovered after production coupling
```

The separately authorized 2026-08-29 extraction adapted the canonical portable
Gearbox core into a public AGPL repository from Taslos Tasks revision
`7734caf208366a0515cf4d78efc17a86363f2238`. The public provenance file records
the exact source and introduction commits. It copied no credentials, private
evidence, host paths, provider configuration, services, databases, product
state, or Durable Supervisor machinery, and the source repository remained
unchanged. Future product adoption still requires public contracts, independent
evidence, explicit versioned adapters, and separate authorization.

## Future consolidation and provenance policy

A later consolidation may occur only after a reviewed plan identifies the exact
source repository, target module, preserved commit/history path, lifecycle and
benchmark evidence mapping, and public-link redirect strategy.

Minimum requirements:

1. Never delete or silently replace the source repository.
2. Preserve commit attribution and cite the original extraction revision.
3. Preserve theory, specification, benchmark, experiment, negative-result, and
   lifecycle history under stable public references.
4. Map each old artifact to a named target module; do not claim the target's
   broader lifecycle from narrow source evidence.
5. Publish an archive/redirect note only after the target is available and the
   mapping is independently checked.
6. Keep citations and public links working or provide explicit redirects.
7. Record rejected consolidation proposals as research history.
8. Execute repository transfer, archive, rename, or deletion only under new
   explicit authority.

## Repository anti-forgetting invariant

The authoritative program registry tracks exactly 21 repositories: 18 concept
repositories, `research`, `site`, and `.github`. Agent Gearbox and Affected
Verification are each mapped exactly once to their public repositories. Concept
tracking does not replace repository tracking.
