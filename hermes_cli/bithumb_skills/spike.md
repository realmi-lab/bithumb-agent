---
name: spike
description: Resolve one technical uncertainty with a bounded disposable experiment.
version: 1.0.0-bithumb
license: MIT
attribution: Adapted from the Hermes Agent spike skill and gsd-build/get-shit-done.
read_only: true
network: false
shell_preprocessing: false
---

# Technical Spike

Use a spike when one unknown blocks a design decision and reading existing code
or documentation is insufficient. A spike produces evidence, not production
code.

## Define one question

Write the uncertainty as a falsifiable question, the constraints that matter,
and the evidence needed for a decision. Set a small time or scope limit.

## Build the smallest experiment

- Isolate the experiment from production paths.
- Use representative inputs and the same boundary that creates uncertainty.
- Measure only what answers the question: compatibility, latency, failure
  behavior, API shape, or implementation feasibility.
- Keep notes so another developer can reproduce the result.

## Decide

End with one of three outcomes:

- feasible under the stated constraints;
- infeasible, with the observed blocker;
- inconclusive, with the next smallest experiment required.

Record evidence, limitations, and how the result changes the implementation
plan. Do not silently ship the prototype as production code. Remove temporary
artifacts only when they are clearly yours and cleanup is authorized; preserve
user work and useful measurements.
