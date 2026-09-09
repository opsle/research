# Post-consolidation evidence inventory

`inventory.json` records default-branch revisions inspected through Git on
2026-09-09. The timestamp denotes the UTC observation date, not a runtime health
probe. `consolidation.json` is the exact parsed final committed Tasks migration
receipt at the revision linked by the inventory. It includes dated partial
observations for provenance; `overall: complete`, `completedAt`, and the final
Durable Supervisor host-move receipt supersede them. Archive paths are provenance
locators, not instructions to restore or reactivate sources.

The inventory includes 11 current repositories and 12 historical sources. Eleven
sources consolidated into Tasks (ten) or Gearbox (one); Durable Supervisor retired
separately. `.github` is retained but its execution project is retired. Repository
presence does not assert that a project is visible, enabled, or currently running.
The manifest's temporary proof projects are not new research repositories.

Current source inspection covered Tasks `docs/TASK_15.md`, `docs/CAPABILITIES.md`,
remote execution proof and no-local-fallback receipt, and the current README and
limitations of Context Firewall, Gearbox, Visible Value and Affected Verification.
The exact revision URLs and retirement commits are in `registry.completed_work`.
Later Taslos Tasks and Paperclip retirement commits supersede the remote proof's
historical statements that predecessor services still existed.

Tasks' historical commit `00d2bac` accepted an external Graphify capability.
The approved Task 21 scope explicitly supplies the final superseding policy:
Graphify is an optional standalone CLI, not a Tasks capability. The current
bundled capability tree contains Gearbox, Context Firewall, Affected Verification
and Visible Value only. This ledger does not claim to inspect or change an external
operator installation, and absence from the bundled tree alone is not evidence
about such installations.

Research maturity is conservative: Context Firewall, Gearbox and Visible Value
remain PROTOTYPED; Affected Verification remains VERIFIED with OBSERVE/SHADOW
research limits. Tasks integration and remote proofs are operational evidence,
not controlled comparative savings or research completion. EXP-001 remains
unconsumed; AV-EXP-002 permanently remains FAIL.

Historical ledger and conceptual analysis are preserved under
`program/history/pre-consolidation/` at research revision
`840c79c04199762acdd59e89e807ca9086f3e45e`. Initial Gearbox publication and all pinned
experiment identities remain unchanged. No deployment, provider experiment,
external task, or PR #18 operation was performed for this reconciliation.
Final verification is delegated to the existing research pipeline.
