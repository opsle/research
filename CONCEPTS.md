# Concept overview

The [theory registry](program/theory-registry.json) and generated
[theory map](program/THEORY_MAP.md) define current concept state. The
[program ledger](program/registry.json) distinguishes current repositories,
consolidated sources, retired concepts and workload eligibility.

There are 19 recorded concepts: seven active standalone concepts, eleven
consolidated concepts, and one retired concept. Eighteen live concepts share eight
current homes. Tasks is program infrastructure and the workload authority;
Visible Value is a standalone concept and receipt-validation CLI.

Ten source concepts have Tasks as their current home: discovery, execution
authorization, recovery, resource claims, scheduler, state ledger, controlled
acceptance, ephemeral workers, event wakeup and verifiable handoff. Routing Policy
is consolidated into Gearbox. Durable Supervisor is retired, with findings
preserved in Tasks and no current conceptual home or activation gate.

Tasks later removed the copied contract archive from its current branch. The
contracts and licenses remain available at the exact historical revisions in
the ledger; consolidation does not prove current implementation fidelity.

Graphify's final role is an optional standalone CLI, not an Opsle Tasks capability.
Task 15's versioned capability contract integrates Gearbox, Context Firewall,
Affected Verification and Visible Value through independent public interfaces.

The [historical bootstrap overview](program/history/pre-consolidation/CONCEPTS.md)
preserves initial SHAs, subordinate concepts and extraction provenance. Its
repository inventory and architectural recommendations are historical, not current
work. Consolidation preserves licenses, experiment identities and negative results;
it does not combine maturity stages or prove comparative benefit.
