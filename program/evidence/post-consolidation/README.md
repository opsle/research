# Post-consolidation evidence inventory

`program/registry.json` remains the sole machine-readable portfolio and priority
authority. This existing inventory is subordinate evidence, not a queue or a
second portfolio. The September 11 reconciliation is recorded under
`registry.reconciliation`; Notebook completion is under the Tasks repository's
`integration_completion.notebook`. No new derived view is introduced.

The previous observation is preserved at
[Research cd1ecf2](https://github.com/opsle/research/blob/cd1ecf2cf28bf057f2ed683ea647d75fd6239e5f/program/evidence/post-consolidation/inventory.json).
`inventory.json` now records the September 11 GitHub default-branch observations.
Its `source` and `source_revision` still identify the immutable September 7
consolidation receipt. `consolidation.json` is unchanged: the final
`overall: complete`, `completedAt` and host-move receipt supersede its dated
partial observations. Archive paths are provenance, not restoration instructions.

All 23 GitHub repositories were checked through repository metadata,
default-branch SHA and exact-revision README reads. All use `main`; 11 current
repositories remain unarchived and all 12 historical sources remain archived.
Context Firewall, Gearbox, Affected Verification, Research and Tasks advanced
since the previous recorded HEADs. Unchanged repositories were rechecked too.
The historical sources' local checkouts can predate their retirement notices;
GitHub supplies their current default-branch identities.

Eleven source concepts consolidated into Tasks (ten) or Gearbox (one); Durable
Supervisor retired separately. Tasks subsequently removed its copied contract
archive in the simplification at
[3baecd46b4e8](https://github.com/opsle/tasks/commit/3baecd46b4e83e4a35bad1f670ae8c5459225d3d).
[Current architecture](https://github.com/opsle/tasks/blob/fc89649edcf80c7cb9399c025d481e79c8ce4eaa/docs/ARCHITECTURE.md)
distinguishes historical migration material from runtime behavior. Exact Git
history retains contracts, licenses and attribution. No concept gains maturity
or an activation requirement from this migration or removal.

Production evidence came from read-only Tasks `GET /api/state`, task details,
durable attempts and `GET /api/health`. Only Research was enabled among current
program projects at the observation; the other workload-eligible program
projects were disabled. `.github` remains a current GitHub repository with a
retired execution project, as do the historical source projects. Runtime
admission flags do not change portfolio membership or priority lanes. Temporary
proof projects and unrelated applications are not research repositories.

Notebook implementation and production integration are complete through
[recovery 482e392086a9e71214699b86491d14b55c8f9aba](https://github.com/opsle/tasks/commit/482e392086a9e71214699b86491d14b55c8f9aba),
[merged PR #83](https://github.com/opsle/tasks/pull/83) and deployed SHA
`fc89649edcf80c7cb9399c025d481e79c8ce4eaa`. The live health response and current
release symlink agree on that SHA. PR #83 explicitly reports 498 passing tests
in a fresh detached exact-SHA suite, zero failures and two existing skips;
46 continuation/lifecycle tests also passed. The pinned
[docs/releases/TASK_60_NOTEBOOK_RECOVERY_2026-09-11.md](https://github.com/opsle/tasks/blob/fc89649edcf80c7cb9399c025d481e79c8ce4eaa/docs/releases/TASK_60_NOTEBOOK_RECOVERY_2026-09-11.md)
corroborates integrated counts, retained-file classification and PR #82
continuation preservation. These are upstream test results, not a new Tasks test
run performed by this ledger reconciliation. Raw private test logs and broker
backup/activation receipts were inaccessible to the execution identity; no
access boundary was changed.

Tasks #51 and #60 remain `FAILED/TEST`: durable attempt records 532/key 2716 and
570/key 3092, with failure events 2760 and 3137. #50 is DONE; umbrella #48 remains
FAILED. Existing #52 is PENDING and blocked by #51, but its mode-controlled inline
completion scope is superseded by recovery. This mismatch does not create a
Notebook retry or replacement. Production state was not modified.

Context Firewall #36 and Affected Verification #23 completed bounded external
package implementations. Their compatibility evidence pins earlier Tasks
revisions; installation and compatibility with current production remain
unproven. Context Firewall's package README explicitly retains a separate
Tasks-owned bundled-removal boundary. Gearbox PR #4 adds provider/model/effort
routing. Visible Value #24/#40 are completed integration repairs. The ledger
preserves failed, cancelled and superseded work independently of those outcomes.

Graphify remains an optional standalone CLI, not a Tasks capability. The four
research measurement interfaces are Gearbox, Context Firewall, Affected
Verification and Visible Value; current Tasks additionally bundles its
product-specific Question Recommendation adapter. Paperclip is intentionally
retained contingency infrastructure by Task #62's approved scope, outside the
portfolio and backlog. Its historical retirement milestone denotes removal from
active orchestration, not decommissioning of the contingency installation. No
contingency health or restoration-readiness check was performed.

No lifecycle or priority-lane promotion is supported. EXP-001 remains PLANNED:
current Research artifacts and inspected durable task history establish no
authorized subject run/result. AV-EXP-002 remains the historical miss;
AV-EXP-003 remains bounded OBSERVE/SHADOW repair evidence. Integration and everyday
telemetry do not establish controlled benefit or independent replication. Site
remains evidence-gated and `.github` still lists historical concept repositories.

The case-insensitive tracked-file search found no accidental Visual Verify
references; the canonical name remains Visible Value. Historical snapshots and
frozen experiment artifacts are unchanged. Only the existing status, priority
and theory views are regenerated; final verification remains with the pipeline.

Verification passed registry validation, generated-view comparison, pinned
offline-freeze qualification and all five existing receipt checks. The Research
unittest suite ran 117 tests: 116 passed, one failed because
`tests/test_validate_program.py:48` still hard-codes the previous Affected
Verification HEAD. Updating that assertion is outside this records-only task;
current evidence was not reverted and the test was not bypassed. This is an
explicit unresolved pipeline blocker, recorded in `registry.reconciliation.verification`.

Opsle Value accounting is in the same verification record. Offline qualification
reproduced 36 Context Firewall invocations (EXACT), 36 Decision Evidence
validations (OBSERVED) and 48 Trajectory Profiler profiles (EXACT). The existing
machine receipts remain unchanged. No subject run, experiment result or causal
savings claim was added.
