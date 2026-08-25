# Legacy maturity labels

The authoritative promotion model is now
[`program/LIFECYCLE.md`](program/LIFECYCLE.md). The labels below are retained to
interpret bootstrap documents and repository READMEs created before the program
ledger. They must not be used for new registry promotions.

Only these exact states are valid:

| State | Meaning |
|---|---|
| IDEA | An observation or question without a falsifiable theory. |
| THEORY | A falsifiable hypothesis and proposed mechanism. |
| PROTOTYPE | A narrow reference implementation exists for interface and correctness testing. |
| TESTING | Controlled experiments are actively producing results. |
| SUPPORTED | Reproducible evidence supports the scoped hypothesis under stated conditions. |
| PROVEN | Sufficiently strong reproducible evidence supports the actual stated hypothesis across its claimed domain. |
| REJECTED | Evidence does not support the hypothesis or the cost/risk defeats it. |
| SUPERSEDED | A later concept/version replaces it while preserving history. |

Existence inside Taslos Tasks never qualifies a concept as PROVEN. Maturity can move backward when evidence or scope changes.
