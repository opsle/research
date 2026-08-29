# EXP-001 offline-freeze qualification evidence

This directory is deterministic provider-free implementation evidence, not an
EXP-001 subject run or result.

The qualification used:

- Context Firewall `953c48f1cfd154d6b7ed10b51b87fe54e4df45f2`;
- Decision Evidence Protocol `b17ae3b41cea7cb0b9e0befe43e885b5aa0e4a09`;
- Agent Trajectory Profiler `0a89661640721d6a39f127514b993d29bd728d47`.

`qualification-report.json` records PASS for six tasks, 12 oracle invocations,
48 provider-free arm renderings, 36 actual Context Firewall reductions, 36
source-backed Decision Evidence validations, and 48 actual trajectory profiles.
It records zero experiment runs and zero provider/model runs.

The remaining files preserve one representative, reproducible chain for the
accepted `chunked` fixture under `bounded-escalating`. Context Firewall measured
6,031 raw bytes and 1,999 initially model-visible bytes: 4,032 bytes initially
avoided (66.85%). The packet was sufficient, so no raw escalation occurred.
Decision Evidence verified the exact source and packet; Agent Trajectory Profiler
reported a valid measured profile with the same raw and visible byte counts and
96 suppressed evidence events.

These are exact/observed implementation-qualification measurements. They do not
establish preserved model correctness, token or cost savings, causal benefit, a
safe context-reduction frontier, or an experiment result. The raw locator in the
receipt is caller supplied; the committed `source-input.json` preserves the
public-safe source bytes for independent verification.

Reproduce and compare every committed artifact with the fail-closed verifier:

```bash
python3 experiments/exp-001/harness.py \
  verify
```

`verify` reruns all 48 arm renderings and byte-compares the canonical report and
all nine representative machine/operator artifacts against this directory.
