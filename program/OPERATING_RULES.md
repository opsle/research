# Program operating rules

Every Opsle execution must:

1. Read `program/registry.json` before selecting or performing work.
2. Verify the relevant repository default branch and HEAD before relying on recorded state.
3. Work against an explicit repository or experiment objective.
4. Preserve immutable or content-addressed evidence for every material claim.
5. Promote lifecycle state only after satisfying the canonical gate in `program/LIFECYCLE.md`.
6. Update the registry when verified state changes.
7. Update the experiment registry when an experiment is planned, run, failed, replicated, or judged.
8. Record blockers and unknowns instead of silently bypassing them.
9. Identify one exact next meaningful task for every touched repository.
10. Return a bounded outcome summary rather than raw execution transcripts.

Run `python3 tools/validate_program.py` and
`python3 tools/render_program_status.py --check` before committing a registry
change.

## Portfolio discipline

New concept repositories must not be created merely because a new idea appears.
Prefer implementing, testing, falsifying, or integrating the existing portfolio.
A genuinely distinct concept requires evidence of independent falsifiability and
reuse, plus separate authorization to create a repository.

Operational integration, deployment, provider use, and product migration are
separate scopes. Registry work does not authorize any of them.
