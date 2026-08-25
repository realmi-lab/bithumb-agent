---
name: plan
description: Produce an evidence-based, file-specific implementation plan before editing.
version: 1.0.0-bithumb
license: MIT
attribution: Adapted from the Hermes Agent planning skill and obra/superpowers.
read_only: true
network: false
shell_preprocessing: false
---

# Implementation Planning

Use this workflow when the user asks for a plan or the change spans several
components. A plan request is read-only unless the user also asks to implement.

## Inspect before deciding

- Identify the repository root, current changes, and applicable instructions.
- Locate the entry points, data flow, tests, configuration, and packaging paths
  that govern the requested behavior.
- Read enough code to name exact files and symbols. Do not invent paths.
- Record material assumptions and unresolved decisions.

## Write an executable plan

For each step, include:

1. The outcome of the step.
2. The exact files or components involved.
3. The behavior or contract to change.
4. The verification that proves the step is complete.

Order steps by dependency. Include migrations, compatibility, documentation,
security, packaging, and rollback only when they apply. Call out user-owned
changes that must be preserved.

## Quality check

A good plan lets another developer implement without rediscovering the whole
system. It distinguishes known facts from choices, names the riskiest boundary,
and ends with targeted plus end-to-end verification. Keep it concise enough to
maintain as the implementation changes.
