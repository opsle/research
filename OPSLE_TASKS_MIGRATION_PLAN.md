# Future Taslos Tasks → Opsle Tasks migration plan

> **NOT AUTHORIZED FOR EXECUTION DURING THIS RUN. PLANNING ONLY.**

Opsle Tasks is the NEXT primary real-world workload after Durable Supervisor
v0.1 is declared and feature-frozen. That workload role does not authorize any
identity, repository, runtime, schema, service, DNS, TLS, provider, or release
migration. The machine-readable program priority remains
`program/registry.json`.

## Intended future identities

- repository: `sneakocom/taslos-tasks` → `opsle/tasks`;
- VPS path: `apps/taslos-tasks` → `apps/opsle-tasks`;
- product: Taslos Tasks → Opsle Tasks;
- host: `tasks.taslos.com` → `tasks.opsle.com`.

Prefer GitHub transfer preserving history, branches, tags, releases, issues/PRs, and redirects. Do not create a fresh repo and copy HEAD. Use `opsle/tasks`, not `opsle/opsle-tasks`.

## Controlled-release classification

Classify every match as Taslos Tasks product reference, Opsle Tasks runtime identity, historical Taslos Tasks evidence, migration compatibility reference, unrelated Taslos product, or unclear. Never globally replace “taslos.” Never rewrite history merely to remove the old name.

## Future inventory

### Repository and GitHub

- transfer, remotes, branches/tags/releases, settings, permissions, rules, Actions, environments, secrets, webhooks, deploy keys, packages, security settings;
- preserve full history and redirects;
- update automation/local remotes only after transfer proof.

### Code and compatibility

- package names and `@taslos/*` → `@opsle/*` where applicable;
- UI/API branding, page titles, source identifiers, documentation, fixtures;
- environment-variable compatibility and deprecation;
- historical and migration-compatible identifiers;
- self-host upgrade/versioning.

### Runtime and infrastructure

- application/release/broker paths, worker names, systemd, Incus projects/profiles/images/networks;
- database names/roles/schema references/migration identities;
- nginx, TLS, DNS, hosted URL, backups, restore, monitoring, alerts, logs, health;
- provider/credential profiles and authorization bindings.

### Release evidence

- exact starting/deployed SHA parity, backup + isolated restore, Global Pause, zero-conflict and queue/lease/schedule/provider census;
- controlled deploy, authenticated smoke, backup/restore, rollback/roll-forward;
- final exact-SHA parity, clean worktrees, historical evidence retention.

## Rename safety and rollback

Define point-of-no-return gates separately for transfer, runtime path, database identity, and DNS. Avoid partial mechanisms that make two identities authoritative. Test restore and rollback at each irreversible boundary.

## Current prohibition

No transfer, visibility change, branch, PR, schema migration, package rename, source edit, service rename, path move, symlink, parallel production copy, Incus rename, nginx/DNS/TLS change, deployment, database/backups/monitoring change, or active branding change is authorized now.

> **NOT AUTHORIZED FOR EXECUTION DURING THIS RUN. A SEPARATE EXPLICIT PROJECT IS REQUIRED.**
