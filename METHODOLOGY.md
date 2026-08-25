# Research methodology

## Lifecycle

Observation → hypothesis → falsifiable requirements → baseline → reference implementation → experiment → correctness gate → efficiency measurement → replication → result → maturity update.

## Required experiment record

Where practical, record model, provider, model version, reasoning effort, tool versions, fixture, prompt, hardware/environment, repetition count, observable tool activity, final result, correctness result, cost/tokens if available, and known confounders.

Never infer or request private chain-of-thought. Use observable prompts, tool calls, files, events, process results, provider-reported usage, and final artifacts.

## Correctness before efficiency

Incorrect candidates are not “efficient.” They remain in the result set but cannot support an efficiency-superiority claim. Every comparison states the exact correctness and safety gate.

## Baselines and replication

A baseline represents a real available alternative, uses the same fixture/outcome definition, and discloses capability differences. Record exact software/configuration revisions, repetitions, and independent environments. Distinguish replicated mechanism from replicated benefit.

## Negative results

Negative, null, failed, and interrupted experiments are retained. Separate harness failure from system-under-test failure and missing data from zero.

## Claims language

Prefer hypothesis, experimental, observed, measured, preliminary, supported, unverified, and not yet established. Avoid revolutionary, breakthrough, solved, guaranteed, eliminated, or proven without evidence meeting the actual claim.
