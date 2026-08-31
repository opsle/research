# EXP-001 entitlement and model-identity readiness evidence

This public-safe bundle records the provider-free qualification of
`experiments/exp-001/readiness-v1` on `2026-08-31`.

The current verdict is `BLOCKED`:

- account entitlement is `UNVERIFIED` because official OpenAI documentation
  does not state that positive model/project metadata guarantees invocation
  through the Responses API;
- model identity is blocked because no distinct immutable dated
  `gpt-5.6-sol` snapshot is published;
- the documentation snapshot identity is
  `sha256:9db99dfec2cb50d105665b29a986ce810446e9f0e933691f05a31282b9e6dcad`;
- its normalized public-facts hash is
  `sha256:5bc678367ba4f1218759ce11d680c4371787c05e7ea553c5f74356f154a17256`.

The source bundle stores minimum normalized facts and official source
identities at
`experiments/exp-001/readiness-v1/documentation-snapshot.json`. It is a
documentation/catalogue snapshot, not a provider model snapshot and not proof
of account entitlement.

The qualification used synthetic metadata only. It made zero authenticated
provider probes, launched zero provider/model subjects, consumed zero
authorizations, and created zero experiment runs, results, or result envelopes.
EXP-001 remains `PLANNED`.

## Opsle dogfooding

The actual Affected Verification `0.1.0` planner consumed a manually normalized
diff, dependency, catalogue, and policy input. Plan
`sha256:649b47f0ac224c347d41c0b28b02131a329802961532df4bc6d9e6273001433d`
classified the plan `SUFFICIENT_BROADENED`, selected 49 of 170 catalogued test
executions plus seven non-test checks, and skipped 121 test executions with
explicit reasons. The public plan is `affected-verification-plan.json`; its
conforming receipt is
`affected-verification-value-receipt.json`. Because the project has no
production Git adapter, the normalized input remains manual evidence and the
plan does not replace policy-required CI.

The actual Decision Evidence generic receipt validator accepted both readiness
receipts with zero violations. The actual Agent Trajectory Profiler `0.3.0`
ingested the readiness receipt as one observational record and emitted seven
visible, safely aggregable exact measurements with summary identity
`sha256:49331ce0336d141133a6878b8794b4475d7bf8eaf0ec59cbba2796ba69d973e2`.
Context Firewall was not run because this work produced no supported tool-output
packet to reduce.
