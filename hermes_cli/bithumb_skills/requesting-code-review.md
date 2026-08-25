---
name: requesting-code-review
description: Review a concrete change for correctness, security, and compatibility risks.
version: 1.0.0-bithumb
license: MIT
attribution: Adapted from the Hermes Agent requesting-code-review skill, obra/superpowers, and MorAlekss.
read_only: true
network: false
shell_preprocessing: false
---

# Requesting Code Review

Use this workflow to review an implementation, patch, or pull request. Review
the actual diff and surrounding contracts; do not infer defects from filenames
alone.

## Establish intent and scope

- Read the request, changed files, and relevant instructions.
- Identify the intended behavior and compatibility promises.
- Inspect nearby callers, tests, configuration, and error paths affected by
  the change.

## Review by risk

Check for:

- incorrect logic, boundary conditions, and stale state;
- unsafe input handling, authorization gaps, secret disclosure, or unintended
  network and process behavior;
- data loss, destructive defaults, race conditions, and resource leaks;
- broken public APIs, file formats, supported Python versions, or packaging;
- missing tests for a concrete failure mode introduced by the change.

Verify each finding against the code. Give it a severity based on realistic
impact and likelihood, cite the narrow location, and describe a practical fix.
Do not inflate style preferences into defects.

## Report

Lead with actionable findings ordered by severity. If none are found, say so
and note meaningful residual risks or untested paths. Do not commit, publish,
or push changes unless the user explicitly asks.
