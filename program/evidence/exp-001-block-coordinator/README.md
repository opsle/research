# EXP-001 provider-free block coordinator evidence

This directory records the secret-backed, provider-free qualification of the
EXP-001 one-block coordinator. It contains no allocation seed, block ID, subject
label, arm assignment, authorization artifact, provider response, experiment
run, or experiment result.

The coordinator prepared the same private block twice in temporary mode and
required byte-identical outputs. Across both passes it validated eight fixture
authorizations, rendered eight subject evidence inputs, prepared eight empty
result-envelope templates, ran six Context Firewall reductions, ran six
Decision Evidence validations, and produced eight Agent Trajectory Profiler
profiles. Temporary private artifacts were destroyed after comparison.

The public block, private-plan, and manifest locators are seed-keyed HMAC
commitments. This prevents enumeration of the 24 possible arm permutations in a
four-arm block. The value receipt records exact counts and zero provider/model
runs without claiming correctness, savings, or experimental benefit.

Fixture authorizations exercise the exact per-label validation path but are
marked `PROVIDER_FREE_FIXTURE`, `fixture_only: true`, and
`provider_launch_permitted: false`. Live preflight requires
`LIVE_PROVIDER_RUN`; therefore the committed qualification is not provider
authorization.
