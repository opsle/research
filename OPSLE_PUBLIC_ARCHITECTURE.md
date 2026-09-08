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
├── gearbox          ← public narrow prototype
├── site
└── tasks            ← current integrated reference implementation
       │
       ▼
tasks.opsle.com      ← current operator host
```

The active repository is `opsle/tasks`. The product does not depend on the
public research runtime.

Opsle Research → independent primitives/experiments → future integration where supported → Opsle Tasks → working integrated reference implementation. The product should prove ideas together, not be their only home.

The intended dependency direction is public Opsle mechanisms and protocols →
Opsle Tasks and other products through versioned adapters.
