# EXP-001 preregistration evidence

This directory records the provider-free verification of EXP-001 launch
preregistration v1. It contains no allocation seed, provider credential, subject
run, provider response, or experiment result.

The verification report binds:

- the exact subject configuration and preregistration identities;
- the public allocation index and encrypted mapping identities;
- secret-backed proof that 60 blocks contain 60 assignments per arm;
- the provider-free fake-transport adapter path and authorization rejection;
- replay of the existing offline freeze through the actual pinned Context
  Firewall, Decision Evidence Protocol, and Agent Trajectory Profiler
  implementations.

The seed-backed verification was performed by the experiment coordinator before
publication. Only the seed commitment and sealed mapping are public. The report
does not make the seed model-visible and cannot independently decrypt the
mapping.

The official OpenAI documentation reviewed for the subject selection was:

- <https://developers.openai.com/api/docs/models/gpt-5.6-sol>
- <https://developers.openai.com/api/docs/guides/latest-model>
- <https://developers.openai.com/api/reference/cli/resources/responses/methods/create>

No distinct dated GPT-5.6 Sol snapshot was listed on 2026-08-29. The
preregistration therefore binds the exact available public identifier and fails
closed on catalogue or parameter drift before launch.
