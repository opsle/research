# Experiments

Use immutable experiment directories with hypothesis, exact fixtures/revisions, provider/model/effort, tools, observable artifacts, correctness, measurements, confounders, result, and maturity impact. Retain failures and negative results.

The canonical experiment index is
[`program/experiments.json`](../program/experiments.json). `EXP-001` is reserved
for the planned Context Firewall experiment and has no measured results.

The provider-free portion of EXP-001 is frozen in [`exp-001/`](exp-001/): six
content-addressed Python repair tasks, a deterministic correctness oracle, four
model-visible evidence arms, a balanced/blinded allocation method whose launch
seed remains unset, and an interoperability qualification harness. This is
benchmark prerequisite evidence, not a subject run or experimental result.
