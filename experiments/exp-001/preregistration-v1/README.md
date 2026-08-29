# EXP-001 launch preregistration v1

Status: `PREREGISTERED_AWAITING_EXACT_BUDGETED_LAUNCH_AUTHORIZATION`.
EXP-001 remains `PLANNED`; this directory contains zero model/provider runs and
zero experiment results.

This append-only preregistration binds the existing offline freeze to one
subject configuration, a fixed repetition and stopping plan, and an instantiated
subject-blinded allocation. It does not mutate the prior offline freeze.

## Subject configuration

The first controlled experiment uses the OpenAI Responses API with
`gpt-5.6-sol`, medium reasoning effort, the standard reasoning mode, default
service tier, no storage, no streaming, and no supplied temperature, `top_p`, or
seed. The official model catalogue lists no distinct dated GPT-5.6 Sol snapshot
as of 2026-08-29. `gpt-5.6-sol` is therefore the exact public identifier frozen
here, with an explicit reproducibility limitation and a mandatory launch-time
catalogue check.

The dependency-free Python subject adapter exposes only `read_file(task.py)` and
`write_file(task.py)`. It has no shell, web, MCP, plugin, skill, subagent,
fallback, retry, or resume path. Evaluator files and allocation material never
enter subject context. Provider response logs and usage remain outside subject
context for later deterministic evaluation and telemetry admission.

The adapter enforces six API calls, eight function calls, 4,096 output tokens
per response, 240,000 request-body bytes, 15 minutes, and a 16,384-byte writable
file. Using the frozen public prices and conservative byte-as-token ceilings,
the registered per-subject spend ceiling is USD 6.30. A pricing increase,
long-context multiplier, model mismatch, missing usage, incomplete response, or
transport failure stops without retry.

## Repetitions and stopping

The fixed plan has six tasks, four arms, and ten repetitions: 60 balanced
task-by-repetition blocks and 240 fresh subjects, 60 per arm. There is no
efficacy or futility stopping. A valid correctness failure is an outcome, not a
reason to stop. Invalid exposure, configuration drift, provider failure,
missing telemetry, interruption, or an incomplete block stops the experiment.
No subject is replaced without a versioned amendment.

The primary comparisons are three paired exact McNemar tests against
`raw-control`, Holm-corrected at alpha 0.05. Per-arm correctness uses 95% Wilson
intervals. This bounded first experiment cannot establish a universal safe
context frontier.

## Blinded allocation

`allocation-index.json` publishes 240 opaque subject labels and no arm identity.
`allocation-mapping.enc` retains the complete mapping encrypted with
AES-256-CBC/PBKDF2. `preregistration.json` commits the random seed, plaintext
mapping, ciphertext, allocation index, configuration, and adapter hashes. The
32-byte seed remains with the human experiment coordinator, outside Git and
outside subject context.

Public verification checks identities, hashes, counts, and absence of arm IDs:

```bash
python3 \
  experiments/exp-001/preregistration-v1/allocation_tool.py \
  verify \
  --index \
  experiments/exp-001/preregistration-v1/allocation-index.json \
  --sealed \
  experiments/exp-001/preregistration-v1/allocation-mapping.enc
```

Secret verification additionally decrypts the mapping, recomputes all 60
blocks, and proves 60 subjects per arm. It requires the coordinator's seed file
and must run outside subject context.

## Provider-free adapter verification

```bash
python3 \
  experiments/exp-001/preregistration-v1/subject_adapter.py \
  verify
```

The provider-free self-test injects a fake transport; it does not authenticate
or call OpenAI. The live `execute` command additionally requires a
non-repository authorization artifact bound to the preregistration identity and
one opaque subject label, permitting exactly one run and accepting the USD 6.30
conservative ceiling. All four label-specific authorizations for one balanced
block must exist before its first subject launches.
Preregistration is not authorization for a 240-subject campaign.
