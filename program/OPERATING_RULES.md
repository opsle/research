# Program operating rules

`program/registry.json` is authoritative for both portfolio state and the
NOW / NEXT / THEN / LATER / PARKED priority state. Generated Markdown is never
an independent planning authority.

Every Opsle execution must:

1. Read `program/registry.json` before selecting or performing work.
2. Verify the relevant repository default branch and HEAD before relying on recorded state.
3. Start from the current program lane and operating question before selecting
   an explicit repository or experiment objective.
4. Preserve immutable or content-addressed evidence for every material claim.
5. Promote lifecycle state only after satisfying the canonical gate in `program/LIFECYCLE.md`.
6. Update the registry when verified state changes.
7. Update the experiment registry when an experiment is planned, run, failed, replicated, or judged.
8. Record blockers and unknowns instead of silently bypassing them.
9. Identify one exact next meaningful task for every touched repository.
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

Run `python3 tools/validate_program.py` and
`python3 tools/render_program_status.py --check` before committing a registry
change. The renderer checks both `PROGRAM_STATUS.md` and
`program/PRIORITY.md`.

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
