# Concept overview

This is the bootstrap narrative and subordinate-concept map. The authoritative
current repository inventory and lifecycle state are in
[`program/registry.json`](program/registry.json); the human-readable generated
view is [`PROGRAM_STATUS.md`](PROGRAM_STATUS.md).

All repositories are public, independently versioned, and part of Opsle Research. Initial SHA means the first public commit created during the 2026-08-25 bootstrap.

| Repository | Maturity | Initial SHA | Implementation | Benchmark |
|---|---:|---|---|---|
| [agent-trajectory-profiler](https://github.com/opsle/agent-trajectory-profiler) | PROTOTYPE | `ce2fd532731d9bf5a0b7a271289bfdcc404f57c1` | sanitized dependency-free prototype | plan and fixtures only; no measured result |
| [semantic-edit-protocol](https://github.com/opsle/semantic-edit-protocol) | THEORY | `29caad5c03827cde17aabd71c38bc25899413a33` | theory/specification only | plan and fixtures only; no measured result |
| [durable-supervisor](https://github.com/opsle/durable-supervisor) | THEORY | `555ebedb992ac74236bb7da8230b4d6b0489830b` | theory/specification only | plan and fixtures only; no measured result |
| [event-driven-agent-wakeup](https://github.com/opsle/event-driven-agent-wakeup) | PROTOTYPE | `a6209860c2151450cc28ed648bc8c2631c8db7ef` | sanitized dependency-free prototype | plan and fixtures only; no measured result |
| [context-firewall](https://github.com/opsle/context-firewall) | THEORY | `e865644e86a3f820a120548e91284c048e515671` | theory/specification only | plan and fixtures only; no measured result |
| [decision-evidence-protocol](https://github.com/opsle/decision-evidence-protocol) | PROTOTYPE | `7050f83406a709da84e4b4770556319f767bbeaf` | sanitized dependency-free prototype | plan and fixtures only; no measured result |
| [agent-state-ledger](https://github.com/opsle/agent-state-ledger) | THEORY | `acab03b1ff7168222552050e21e7553b07d00e7c` | theory/specification only | plan and fixtures only; no measured result |
| [agent-scheduler-runtime](https://github.com/opsle/agent-scheduler-runtime) | THEORY | `d97cd3c218b20e0b2b0e09873f6a3d15c396b3a0` | theory/specification only | plan and fixtures only; no measured result |
| [verifiable-agent-handoff](https://github.com/opsle/verifiable-agent-handoff) | PROTOTYPE | `399e5cfae94345affa3f087f0f6eb9e77669d33c` | sanitized dependency-free prototype | plan and fixtures only; no measured result |
| [agent-routing-policy](https://github.com/opsle/agent-routing-policy) | THEORY | `43fc2a72d2c8494b2dcdca7b5a209de61d8fe2d8` | theory/specification only | plan and fixtures only; no measured result |
| [agent-resource-claims](https://github.com/opsle/agent-resource-claims) | THEORY | `dfe0fbc90c67ce5ef4256354bb62f1d511b1304c` | theory/specification only | plan and fixtures only; no measured result |
| [agent-discovery-control](https://github.com/opsle/agent-discovery-control) | THEORY | `926547dd9fd713990b1d6f1f2e650aa6c0883564` | theory/specification only | plan and fixtures only; no measured result |
| [agent-execution-authorization](https://github.com/opsle/agent-execution-authorization) | THEORY | `8fb02e943c83fae121c63185d2f0d0dde8c4260a` | theory/specification only | plan and fixtures only; no measured result |
| [controlled-agent-acceptance](https://github.com/opsle/controlled-agent-acceptance) | THEORY | `2d652adf56e53953327d09b1ba9c4a9c3445f052` | theory/specification only | plan and fixtures only; no measured result |
| [agent-recovery-policy](https://github.com/opsle/agent-recovery-policy) | THEORY | `1b733a111e26e0a409fee3b96f627048531daefe` | theory/specification only | plan and fixtures only; no measured result |
| [ephemeral-agent-workers](https://github.com/opsle/ephemeral-agent-workers) | THEORY | `ad96fcfdfac06d340b5e96d369634980cee78ef4` | theory/specification only | plan and fixtures only; no measured result |

## Ecosystem repositories

| Repository | Purpose | Initial SHA |
|---|---|---|
| [opsle/site](https://github.com/opsle/site) | Source foundation for future opsle.com; not deployed | `85c3bc7c04f6a2774d589a65df008ad1f8837794` |
| [opsle/.github](https://github.com/opsle/.github) | Organization profile | Recorded in that repository |

## Subordinate concepts

These mechanisms remain inside parent projects until they show independent falsifiability, a reusable interface, and meaningful independent install/removal value.

| Concept | Parent / current role |
|---|---|
| Mutation Amplification | agent-trajectory-profiler metric |
| Edit Payload Amplification | agent-trajectory-profiler metric |
| Semantic Region Revisit Rate | agent-trajectory-profiler metric |
| Change Intent Graph | semantic-edit-protocol mechanism |
| failure-only test reporting | context-firewall reducer |
| semantic Git adapter | decision-evidence/context-firewall adapter |
| semantic shell adapter | decision-evidence/context-firewall adapter |
| provider result envelope | decision-evidence-protocol adapter |
| evidence-gated completion | decision-evidence + state-ledger policy |
| already-satisfied proof | agent-discovery-control mechanism |
| Global Pause | agent-scheduler-runtime safety gate |
| provider cooldown registry | routing/scheduler evidence source |
| execution-target snapshots | authorization/routing binding |
| project configuration snapshots | state-ledger/authorization binding |
| independent reviewer routing | routing/controlled-acceptance mechanism |
| fresh-worker remediation | ephemeral-workers/recovery mechanism |
| objective graph planner | durable-supervisor/discovery mechanism |
| multi-agent write-region coordination | semantic-edit/resource-claims bridge |
| PLAN/DESIGN/BUILD/REVIEW/TEST pipeline | historical scheduler experiment, not final architecture |
| universal redaction | subordinate defense; never a substitute for authorization |
| provider availability countdown | routing UI projection |
| durable route-reason UI | routing evidence presentation |

## Promotion rule

Promote only with independent falsifiability, an independent reusable interface, and meaningful independent install/removal value. Rejected and superseded concepts remain recorded.
