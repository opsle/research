# Future hosted plan

> Planning only. No SaaS infrastructure, DNS, production secret, or hosted product was implemented.

## Product shapes

1. Single-user reference instance with self-host parity.
2. Possible multi-tenant service only after isolation evidence.
3. `tasks.opsle.com` as future reference host; possible `app.opsle.com` remains a later decision.

## Concerns

- tenant identity and data/compute isolation;
- provider credentials, least privilege, rotation, non-retention;
- quotas, provider budgets, metering, billing, dispute evidence;
- hosted worker fleet, sandboxing, resources, network, destruction proof;
- GitHub Apps/installations, repository authorization, revocation, webhook integrity;
- storage, evidence retention, backups, restore, disaster recovery;
- audit, observability, SLOs, incident response, abuse controls, rate limits;
- privacy, classification, retention/deletion, export;
- hosted ↔ self-host migration;
- regional placement, availability, graceful degradation.

Never mix tenant credentials, repositories, artifacts, workers, claims, logs, or evidence. A worker receives only one bounded target/authority. The privileged broker remains narrow.

Hosted state exports with versioned schemas and evidence digests so users can leave without losing work history or provenance.
