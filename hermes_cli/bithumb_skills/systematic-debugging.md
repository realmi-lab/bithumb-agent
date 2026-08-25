---
name: systematic-debugging
description: Reproduce, isolate, fix, and verify defects from evidence.
version: 1.0.0-bithumb
license: MIT
attribution: Adapted from the Hermes Agent systematic-debugging skill and obra/superpowers.
read_only: true
network: false
shell_preprocessing: false
---

# Systematic Debugging

Use this workflow when behavior is wrong, intermittent, or not yet explained.
The goal is a demonstrated cause and a verified fix, not a plausible guess.

## 1. Reproduce the failure

- Record the smallest reliable command, input, and environment that fails.
- Capture the exact error, exit status, logs, and affected version.
- Separate observed facts from assumptions.
- If the failure is intermittent, identify what varies between passing and
  failing runs before changing code.

## 2. Trace the failing path

- Read the entry point and follow data and control flow to the failure.
- Compare the failing path with a nearby working path when one exists.
- Inspect configuration, boundaries, and recent changes that can alter it.
- Add narrow diagnostics only when existing evidence cannot distinguish the
  leading hypotheses. Do not expose secrets in diagnostics.

## 3. Rank hypotheses

Write a short list ordered by likelihood and impact. For each hypothesis,
state the observation that would confirm or reject it. Test one variable at a
time so the result remains interpretable.

## 4. Apply the smallest causal fix

- Change the point that violates the expected contract.
- Avoid unrelated cleanup while the defect is still being isolated.
- Preserve existing user changes and public behavior outside the bug.
- Add a regression test that fails for the original reason when practical.

## 5. Verify

- Re-run the original reproduction.
- Run the closest targeted tests, then broader relevant checks.
- Check adjacent error paths and compatibility boundaries.
- Report the cause, evidence, changed behavior, and any remaining uncertainty.

If evidence disproves the current theory, return to the trace. Do not stack
speculative fixes until the failure disappears by accident.
