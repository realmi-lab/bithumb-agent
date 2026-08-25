# Open-source customization notice

Bithumb Agent is a modified distribution derived from Hermes Agent:

- Upstream project: https://github.com/NousResearch/hermes-agent
- Upstream copyright: Copyright (c) 2025 Nous Research
- License: MIT (`SPDX-License-Identifier: MIT`)
- Customization maintainers: Bithumb Agent contributors
- Contact: ilhong.kim@bithumbcorp.com

The original MIT license and copyright notice are preserved in `LICENSE`.
Bithumb-specific modifications are distributed under the same MIT License.

The modifications include the `bithumb-agent` package and command name, orange
CLI identity, Bithumb onboarding and `/bit` commands, OAuth-only provider
selection, standalone ChatGPT/Codex browser OAuth, Google Antigravity CLI
integration, a restricted local coding-tool policy, removal or exclusion of
managed gateway/skill-tool distribution paths, Python 3.14 compatibility, and
packaging/security regression tests. A detailed change and provenance record is
provided in `CUSTOMIZATION.md`.

Parts of the command-line experience are inspired by Google Antigravity. Google
Antigravity source code is not claimed as part of this repository, and its
separately installed executable remains subject to its own terms.

This repository is an independent open-source customization and is not an
official Bithumb product or official distribution. Bithumb, Hermes Agent, Nous
Research, Google, Antigravity, OpenAI, ChatGPT, Codex, and other names and marks
belong to their respective owners.

This notice supplements, but does not replace or modify, the MIT License.
