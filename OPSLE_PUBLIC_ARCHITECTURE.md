# Future public architecture

```text
                    OPSLE
opsle.com
│
├── thesis
├── research
├── concepts
├── experiments
├── benchmarks
├── failures
├── documentation
└── product
       │
       ▼
github.com/opsle
│
├── research
├── concept repositories
├── gearbox          ← RECOMMENDED FUTURE repository; not created
├── site
└── tasks            ← FUTURE migration, not current
       │
       ▼
tasks.opsle.com      ← FUTURE canonical host, not current
```

The active repository remains `sneakocom/taslos-tasks`; the active path remains `apps/taslos-tasks`. Neither depends on public research.

Opsle Research → independent primitives/experiments → future integration where supported → Opsle Tasks → working integrated reference implementation. The product should prove ideas together, not be their only home.

The intended dependency direction is public Opsle mechanisms and protocols →
future Opsle Tasks and other products through versioned adapters. Private Taslos
Tasks implementation complexity is historical provenance and feasibility
evidence, not the canonical home for general mechanisms.
