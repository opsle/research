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

- [CONCEPTS.md](CONCEPTS.md) — public registry and subordinate concepts.
- [METHODOLOGY.md](METHODOLOGY.md) — evidence and experiment rules.
- [MATURITY.md](MATURITY.md) — exact maturity states.
- [ARCHITECTURE.md](ARCHITECTURE.md) — cross-repository system map.
- [OPSLE_EXTRACTION_MAP.md](OPSLE_EXTRACTION_MAP.md) — read-only source audit and provenance.
- [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) — what remains unanswered.
- [OPSLE_SITE_PLAN.md](OPSLE_SITE_PLAN.md) — future opsle.com content architecture.

## Product relationship

Opsle Tasks is the future public name of the integrated reference implementation currently under active development as Taslos Tasks. Its repository transfer, runtime rename, publication, and hosting migration are intentionally deferred.

There is no dependency edge from the active Taslos Tasks system to these repositories.

## Integrity

Hypotheses are not facts. Feasibility in one application does not prove general superiority. Negative and failed experiments remain part of the record. No private chain-of-thought is collected; experiments use observable artifacts only.

## License

Apache-2.0. No active-product code was copied, so no known licensing conflict requires a deviation.
