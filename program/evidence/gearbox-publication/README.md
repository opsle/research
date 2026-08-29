# Gearbox publication interoperability evidence

This directory records read-only consumption of the public Gearbox release-001
Visible Value receipt by exact revisions of two mature Opsle mechanisms.

- Decision Evidence Protocol validated the generic `opsle.value-receipt.v1`
  structure with zero violations.
- Agent Trajectory Profiler validated and summarized the same receipt as one
  observational run.

The input receipt is preserved in `opsle/gearbox`; these records bind it by
SHA-256 and public locator. Context Firewall was not run because the only
current adapter accepts a strict TAP subset, not this Gearbox fixture. No token,
cost, latency, correctness, comparative, causal, or avoided-session claim is
made.
