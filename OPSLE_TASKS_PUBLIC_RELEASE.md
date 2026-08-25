# Future Opsle Tasks public release

> Planning only. Taslos Tasks remains private in its existing location. Publication was not executed.

## Full-history audit

Audit every reachable commit, tag, branch, release asset, PR artifact, LFS object, submodule reference, and archive for credentials, tokens, private keys, connection strings, private addresses, environment secrets, database data, backups, logs, sensitive screenshots, and accidental artifacts. Removing a value from HEAD is insufficient if reachable history retains it.

## Security

Review authentication, authorization, external operator API, worker authority, broker, credential transport, arbitrary execution, path traversal, shell/SQL injection, SSRF, filesystem exposure, debug endpoints, deployment authority, redaction, and unsafe defaults.

Server-side identity/current grants are authoritative. Never trust client-provided user, role, project, permission, approval, worker, lease, fence, or source identity. UI hiding is secondary.

## Self-hostability

Users should be able to clone, configure, install, connect providers, create project/objective/task, execute isolated work, verify, review, observe, back up, restore, and upgrade without private infrastructure.

## Documentation

Require README, architecture, threat model, installation, configuration, providers, development, deployment, backup, restore, upgrade, troubleshooting, contribution, security, license, release/versioning.

## Eligibility

- development/readiness gate = PASS;
- production release verified;
- exact repository/deployment parity;
- required tests pass;
- security audit passes;
- full-history secret audit passes;
- self-host docs sufficient;
- license complete;
- no known publication blocker.

Visibility changes only in the separately authorized release project. It did not change during this bootstrap.
