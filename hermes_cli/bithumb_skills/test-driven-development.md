---
name: test-driven-development
description: Build behavior through a failing test, minimal implementation, and refactoring.
version: 1.0.0-bithumb
license: MIT
attribution: Adapted from the Hermes Agent TDD skill and obra/superpowers.
read_only: true
network: false
shell_preprocessing: false
---

# Test-Driven Development

Use this workflow for behavior changes where an automated test can express the
contract. Keep the loop proportional to the change.

## Red: express one behavior

- Choose the smallest observable behavior that should change.
- Add or adjust one focused test using the public boundary when possible.
- Run it and confirm it fails for the intended reason, not because of a typo,
  missing fixture, or broken environment.
- If it already passes, strengthen the assertion or verify that code changes
  are actually required.

## Green: implement only what is needed

- Make the smallest production change that satisfies the failing test.
- Re-run the focused test until it passes.
- Do not add speculative abstractions, options, or unrelated cleanup.

## Refactor: improve without changing behavior

- Remove duplication and clarify names or structure while tests stay green.
- Run the focused test after each meaningful refactor.
- Then run the surrounding suite and relevant static or packaging checks.

## Practical exceptions

Generated files, documentation-only edits, emergency diagnostics, and short
experiments may not benefit from a strict red-green loop. In those cases,
state the reason and use the closest reliable verification. Never delete or
weaken an existing test merely to make a change pass without explaining the
contract change.

Finish by reporting which behavior the test protects and which checks ran.
