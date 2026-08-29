# Opsle Research

> **What if we stopped using intelligence for work that doesn’t require intelligence?**

Opsle researches how much work in agentic AI actually requires model cognition and how much can be safely moved into deterministic systems.

## Operating rule

```text
DOES THIS OPERATION REQUIRE COGNITION?
                 │
            ┌────┴────┐
            │         │
           YES        NO
            │         │
          MODEL    SOFTWARE
            │         │
            └────┬────┘
                 │
              MEASURE
```

When the answer is unclear: experiment → measure correctness → measure efficiency → keep, change, or reject.

## Research lifecycle

Discover → isolate → formalize → specify → falsify → benchmark → publish → optionally integrate later.

Important mechanisms should remain understandable, falsifiable, benchmarkable, reusable, removable, and traceable outside a large product.

## Start here

- [PROGRAM_STATUS.md](PROGRAM_STATUS.md) — generated 20-repository dashboard.
- [program/registry.json](program/registry.json) — authoritative machine-readable ledger.
- [program/THEORY_MAP.md](program/THEORY_MAP.md) — canonical conceptual topology and Gearbox boundary.
- [program/theory-registry.json](program/theory-registry.json) — machine-readable concept classifications and dispositions.
- [program/experiments.json](program/experiments.json) — canonical experiment registry.
- [experiments/exp-001/](experiments/exp-001/) — frozen provider-free EXP-001 benchmark and launch preregistration with zero subject/model runs.
- [program/evidence/exp-001-preregistration/](program/evidence/exp-001-preregistration/) — provider-free allocation, adapter, interoperability, and Visible Value verification.
- [program/LIFECYCLE.md](program/LIFECYCLE.md) — evidence gates for lifecycle promotion.
- [program/OPERATING_RULES.md](program/OPERATING_RULES.md) — mandatory execution rules.
- [CONCEPTS.md](CONCEPTS.md) — concept overview and subordinate concepts.
- [METHODOLOGY.md](METHODOLOGY.md) — evidence and experiment rules.
- [MATURITY.md](MATURITY.md) — legacy bootstrap maturity labels.
- [ARCHITECTURE.md](ARCHITECTURE.md) — cross-repository system map.
- [OPSLE_EXTRACTION_MAP.md](OPSLE_EXTRACTION_MAP.md) — read-only source audit and provenance.
- [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) — what remains unanswered.
- [OPSLE_SITE_PLAN.md](OPSLE_SITE_PLAN.md) — future opsle.com content architecture.

Validate ledger integrity with `python3 tools/validate_program.py`. Regenerate the
dashboard with `python3 tools/render_program_status.py`.

## Product relationship

Opsle Tasks is the future public name of the integrated reference implementation currently under active development as Taslos Tasks. Its repository transfer, runtime rename, publication, and hosting migration are intentionally deferred.

The public Gearbox core was adapted with exact provenance from Taslos Tasks, but
the active product has no runtime dependency edge on the public repositories.

## Integrity

Hypotheses are not facts. Feasibility in one application does not prove general superiority. Negative and failed experiments remain part of the record. No private chain-of-thought is collected; experiments use observable artifacts only.

## License

This research control plane is Apache-2.0. The separately released Gearbox
repository preserves the predecessor's AGPL-3.0-only license and provenance.
