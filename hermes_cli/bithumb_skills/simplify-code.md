---
name: simplify-code
description: Reduce accidental complexity while preserving observable behavior.
version: 1.0.0-bithumb
license: MIT
attribution: Adapted from the Hermes Agent simplify-code skill, inspired by Claude Code simplify.
read_only: true
network: false
shell_preprocessing: false
---

# Simplify Code

Use this workflow after functionality works or when the user explicitly asks
for simplification. The success criterion is easier maintenance with unchanged
observable behavior.

## Establish the boundary

- Start from the requested files or current diff.
- Identify public APIs, persistence formats, error behavior, and performance
  characteristics that must remain stable.
- Confirm relevant tests pass before restructuring when practical.

## Simplify deliberately

- Remove duplicated logic only when the shared concept is real.
- Flatten unnecessary nesting with clear guard clauses.
- Replace indirect control flow with direct names and explicit data flow.
- Delete dead code only when references and compatibility requirements have
  been checked.
- Prefer a small local helper over a new framework or abstraction layer.

## Guardrails

- Do not mix unrelated style changes into the same patch.
- Do not change an API merely because another shape looks cleaner.
- Do not overwrite user changes or generated artifacts unexpectedly.
- Keep comments that explain constraints; remove comments that only restate
  obvious syntax.

Run focused tests after each structural change and broader relevant checks at
the end. Summarize what became simpler and how behavior preservation was
verified.
