# EXP-001 provider-free block coordinator v1

Status: `PROVIDER_FREE_QUALIFIED_NO_SUBJECT_RUN`.

This coordinator prepares exactly one four-arm EXP-001 block. It never calls a
provider. It unseals the allocation outside subject context, validates the four
label-bound authorization artifacts, materializes the frozen arm evidence, and
writes private deterministic result-envelope templates whose provider and
correctness fields remain empty.

The private output contains the arm mapping. It must stay outside Git, outside
every subject workspace, and outside model-visible subject context. Canonical
stdout contains only commitments and exact counts. A named operator indicator
is emitted separately on stderr.

## Live preflight contract

`preflight` requires:

- the external coordinator seed;
- one public block ID from `allocation-index.json`;
- exactly four authorization JSON files named `<subject-label>.json`;
- an absent destination directory on a private filesystem;
- the exact registered subject environment.

Each live authorization must satisfy the preregistered one-run and USD 6.30
ceiling and additionally bind `LIVE_PROVIDER_RUN`, the block ID, and the subject
configuration. The command validates authorization but does not consume it and
does not launch the subject adapter.

## Provider-free qualification

`qualify` uses four explicitly fixture-only authorizations and runs the same
secret-backed preflight twice. It requires byte-identical private artifacts and
summaries. The temporary outputs are destroyed after comparison. No fixture
authorization can pass the live preflight class gate.

The public block commitment is an HMAC keyed by the external seed; a plain hash
would permit enumeration of the 24 possible four-arm permutations. The
committed qualification report and value receipt are in
`program/evidence/exp-001-block-coordinator/`. They disclose commitments and
counts, not the allocation seed, selected labels, block ID, or arm mapping.

## Claim boundary

This implementation proves provider-free coordinator behavior only. It is not
an EXP-001 run or result, does not authorize a provider call, does not establish
model correctness, and does not make a token, cost, latency, or causal-savings
claim.
