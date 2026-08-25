# Cross-repository architecture

```text
                    DURABLE SUPERVISOR
                           │
                    STATE LEDGER
                           │
                   SCHEDULER RUNTIME
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
RESOURCE CLAIMS      ROUTING POLICY      RECOVERY POLICY
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                EXECUTION AUTHORIZATION
                           │
                  EPHEMERAL WORKER
                           │
                SEMANTIC EDIT PROTOCOL
                           │
                VERIFIABLE HANDOFF
                           │
         ┌─────────────────┴──────────────────┐
         │                                    │
 CONTEXT FIREWALL                    INDEPENDENT REVIEW
         │                                    │
         └─────────────────┬──────────────────┘
                           │
                DECISION EVIDENCE
                           │
                           ▼
                      SUPERVISOR
```

Measurement: observable execution → agent-trajectory-profiler → correctness / mutation / tokens / cost / time.

Discovery: agent stages → discoveries → discovery control → bounded admitted work.

Controlled testing: controlled-agent-acceptance → exact authority envelope → real system → durable evidence → accept/reject.

## Compatibility and removal

Each core accepts generic input and emits generic output. No primitive depends on a Taslos Tasks database, worker, scheduler, package, path, or production infrastructure. Host-specific adapters remain optional. Where evidence later supports use: install → configure adapter → enable → benchmark; disable/remove returns the host to baseline.
