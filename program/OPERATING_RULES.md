# Program operating rules

`program/registry.json` is authoritative for research portfolio state and evidence-driven priority lanes. Opsle Tasks (`opsle/tasks`) is authoritative for current workload, task management and execution. Lanes describe research priorities; they do not create a parallel queue. Generated Markdown is never an independent planning authority.

Every Opsle execution must:

1. Use the authorized Opsle Tasks record to select work; consult `program/registry.json` for research evidence and scope.
2. Verify the relevant repository default branch and HEAD before relying on recorded state.
3. Reconcile the authorized task with the operating question and current repository membership; historical sources are not activation candidates.
4. Preserve immutable or content-addressed evidence for every material claim.
5. Promote lifecycle state only after satisfying the canonical gate in `program/LIFECYCLE.md`.
6. Update the registry when verified state changes.
7. Update the experiment registry when an experiment is planned, run, failed, replicated, or judged.
8. Record blockers and unknowns instead of silently bypassing them.
9. Record a justified next action for current repositories; historical sources have no active next task.
10. Return a bounded outcome summary rather than raw execution transcripts.
11. When any Opsle mechanism runs, preserve its machine-readable Visible Value
    receipt and keep its named operator indicator outside canonical model
    context.
12. Include a dedicated `Opsle Value` section in the execution summary naming
    each mechanism used, whether it ran, the exact or observed result,
    measurement class, and useful evidence reference. Missing measurements stay
    missing; do not fabricate zeroes or savings.
13. Classify everyday telemetry as observational. Do not relabel an accumulated
    production corpus as causal or `EXPERIMENTAL` evidence without the controlled
    method required by `program/VISIBLE_VALUE_CONTRACT.md`.
14. Do not create a work item solely because an implementation can be improved.
    New work normally requires a violated invariant, demonstrated defect,
    measured inefficiency, missing capability blocking the current program
    objective, experiment requirement, security or safety issue, or externally
    required release condition.
15. Park cosmetic cleanup, architectural taste, hypothetical robustness, and
    speculative future requirements unless qualifying evidence appears.

Registry changes require the CI integrity checks: `python3 tools/validate_program.py`, `python3 tools/render_program_status.py --check`, the research unittest suite, and existing offline-freeze and receipt checks with pinned dependencies. The renderer updates `PROGRAM_STATUS.md`, `program/PRIORITY.md`, and `program/THEORY_MAP.md` together. Task-specific execution instructions may leave final verification to the pipeline.

## Portfolio discipline

New concept repositories must not be created merely because a new idea appears.
Prefer implementing, testing, falsifying, or integrating the existing portfolio.
A genuinely distinct concept requires evidence of independent falsifiability and
reuse, plus separate authorization to create a repository.

Operational integration, deployment, provider use, and product migration are
separate scopes. Registry work does not authorize any of them.

## Operator and model channels

Operator-visible telemetry is not automatically decision-relevant model
context. CLI mechanisms should keep canonical decision-relevant machine JSON on
stdout and emit a single concise, stably named indicator on stderr at a
meaningful transition or completion point. A full machine value receipt may use
a caller-requested deterministic sidecar when embedding it would inflate compact
model context. Display timestamps, ambient repository state, and other
nondeterministic fields must not contaminate deterministic semantic output.

## Retirement and current ownership

Durable Supervisor, Taslos Tasks and historical agent-run are retired. Their archived controls, migration rollback notes and experiments authorize no current work. Paperclip is intentionally retained contingency infrastructure, outside the research portfolio and backlog; removal from active Tasks orchestration did not establish contingency decommissioning. Completed consolidation receipts supersede dated partial observations. Graphify is an optional standalone CLI, not a Tasks capability. Do not recreate retired repositories or execution systems from stale references.

Repository activity, Tasks project visibility and research maturity are independent. `.github` is retained for housekeeping but excluded from workload eligibility. Consolidated concepts share active homes; historical source records retain evidence without becoming active dependencies. Release and data-safety requirements remain separate from task authorization.

Recovery can complete an implementation and its production integration while the
original execution remains failed. Notebook recovery through Tasks PR #83 does
not rewrite #51/#60, activate the overlapping pending #52, or complete a research
lifecycle. Use the revision-linked recovery and dated history in `registry.json`
when judging whether work is already implemented. Do not create retry or
replacement work from a failed status alone.
