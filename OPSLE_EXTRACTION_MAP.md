# Opsle extraction map

> Historical extraction record. The 16 candidates below preserve what was
> isolated from the predecessor snapshot; they are not the canonical future
> repository/product topology. See
> [`program/THEORY_MAP.md`](program/THEORY_MAP.md) for the 2026-08-29 source
> reconciliation, the restored Agent Gearbox definition, and recommended
> dispositions. No repository action followed from that reconciliation.

## Read-only snapshot

- Source: Taslos Tasks, active predecessor of future Opsle Tasks.
- Repository: `sneakocom/taslos-tasks` (private; unchanged).
- Commit inspected: `e2b061dd4ee1404ef59b27a9a76bf97a8fbbde1c`.
- Inspection timestamp: `2026-08-25T03:15:01Z`.
- History: 148 commits enumerated; latest 40 subjects and failure/correction sequence reviewed.
- Corpus: 260 supported files — 217 code and 43 documents; 44 test files identified.
- Graphify: deterministic AST extraction plus two bounded, read-only Antigravity subscription CLI semantic passes. No Gemini/Google API key or separately metered Google API was used.
- Graph: 1,839 nodes, 3,673 retained edges, 207 communities. Health warning: 395 dangling extraction edges and 169 same-endpoint collapses; retrieval support, not source truth.

## Areas inspected

README, PROJECT_STATE, architecture/decisions, migration/readiness evidence, recent commit history, relational schema/migrations, worker/lease supervisor, backends/broker/sealed-result store, routing/provider availability, authorization/redaction, recovery, discovery/planning, provider adapters/result parser, result envelopes, independent review, verification runner, resource catalog/claim sets/fencing, schedules/Global Pause, target/config snapshots, operational metrics, and tests.

No live database, provider state, schedule, Pause control, worker, broker, Incus object, service, nginx, DNS, TLS, deployment, or active checkout file was modified or used as a semantic-write target.

## Classification

- **A** standalone public project candidate.
- **B** subordinate mechanism.
- **C** ordinary Taslos Tasks product feature.
- **D** implementation detail.
- **E** promising but insufficiently understood.

## A — standalone candidates created

| Candidate | Source observation | Generalized invariant | Extraction |
|---|---|---|---|
| agent-trajectory-profiler | observable execution/session artifacts and metrics | correctness gates efficiency | sanitized prototype + tests |
| semantic-edit-protocol | editing/transport research question | bounded preconditioned transactions | theory/spec |
| durable-supervisor | objectives/jobs/events/reconstruction | decisions separate from runner lifecycle | theory/spec |
| event-driven-agent-wakeup | jobs/events/schedules | ordinary waiting uses zero model inference | sanitized prototype + tests |
| context-firewall | bounded context/redaction/evidence | decision evidence with raw escalation | theory/spec |
| decision-evidence-protocol | structured result/verification/metrics envelopes | minimal vendor-neutral facts | sanitized prototype + tests |
| agent-state-ledger | relational state/append-only events/runs | work survives conversation loss | theory/spec |
| agent-scheduler-runtime | queues/dependencies/schedules/leases/Pause | mechanical orchestration is runtime work | theory/spec |
| verifiable-agent-handoff | broker/seals/handoff evidence | seal before cleanup; reconstruct after destruction | sanitized prototype + tests |
| agent-routing-policy | provider pool/roles/strict routes | routes are purpose-bound and explained | theory/spec |
| agent-resource-claims | catalog/claim sets/renewal/takeover | stale processes lose authority | theory/spec |
| agent-discovery-control | admission/storm limits/already_satisfied | proposals converge without churn | theory/spec |
| agent-execution-authorization | worker subject/authorization service | source and current authority differ | theory/spec |
| controlled-agent-acceptance | versioned controller/one-shot CAS | non-reusable exact authority | theory/spec |
| agent-recovery-policy | typed failures/bounded ladder | every failure path shares budgets | theory/spec |
| ephemeral-agent-workers | broker/workers/destruction state | seal, terminate, destroy, prove | theory/spec |

## B — subordinate mechanisms

Mutation Amplification, Edit Payload Amplification, Semantic Region Revisit Rate, Change Intent Graph, failure-only test reporting, semantic Git/shell adapters, provider result envelope, evidence-gated completion, already-satisfied proof, Global Pause, provider cooldown registry, execution-target and project-configuration snapshots, independent reviewer routing, fresh-worker remediation, objective graph planner, multi-agent write-region coordination, PLAN/DESIGN/BUILD/REVIEW/TEST pipeline, universal redaction, provider availability countdown, and durable route-reason UI.

## C — ordinary product features

Objective/task/project CRUD, dashboard views, schedule editing UI, user/security administration surfaces, maintenance schedule definitions, application-specific bootstrap records, and Taslos Tasks operator workflows.

## D — implementation details

Fastify route layout, React components, Drizzle migration filenames, PGlite/native PostgreSQL harness wiring, Incus command syntax, systemd/nginx names, concrete tables, broker paths, and package identities.

## E — promising but insufficiently understood

| Finding | Why E | Next evidence |
|---|---|---|
| Verified-knowledge promotion boundary | optimal trust/relevance policy unknown | adversarial contamination benchmark |
| Revisioned objective-graph replanning | value versus simpler graphs unmeasured | planning fixtures + churn metrics |
| Release interruption model | exact-SHA rollback/restart evidence may not port | cross-runtime study |
| Reviewer independence strength | enforceable but correctness impact unmeasured | blinded same/different-provider review |
| Source-destruction correlation effect | reconstruction works; correlated-error effect unknown | controlled verifier experiment |

## Failure-derived narratives

### Fenced claim-set transition

Original assumption → successful lease renewal was sufficient.  
Observed failure → a client-side exact-claim query failed after provider success.  
Violated invariant → job/owner/lease/task/project/target/execution/stage/claims/catalog/access/fence were not one stable binding.  
Corrected invariant → server-time predicates, complete typed binding, safe failure class.  
Regression evidence → native PostgreSQL, replay, drift, and redaction tests.  
Remaining uncertainty → portable store semantics.

### Result lost during correct cleanup

Original assumption → credential removal before destruction preserved enough evidence.  
Observed failure → the only result commit lived in the disposable worker and was garbage-collected.  
Corrected invariant → authenticated atomic manifest + thin bundle before cleanup, with exact commit/tree/delta/result binding and restart rehydration.  
Regression evidence → source deletion/restoration and tamper/missing-object/unsafe-path rejection.  
Remaining uncertainty → non-Git formats and byte ceilings.

### Immutable source versus current continuation

Original assumption → continuation could reuse/rewrite source authority.  
Observed failure → takeover needed a new fence while preserving old source seal/fence identity.  
Corrected invariant → immutable source authority and current continuation authority are jointly revalidated, separate capabilities.  
Remaining uncertainty → smallest portable contract.

### Purpose-specific independent review

Original assumption → broad controlled execution routing covered review.  
Observed failure → review needed its own purpose, provider/profile/default model/availability revision, source seal, and one-shot pre-launch CAS.  
Corrected invariant → authorize exact review before workspace, credential, or provider process.  
Remaining uncertainty → measured quality benefit.

## Snapshot caution

The active repository may evolve after `2026-08-25T03:15:01Z`. Implementation-detail claims are scoped to `e2b061dd4ee1404ef59b27a9a76bf97a8fbbde1c`.
