# Bithumb Agent customization record

## 1. Source and license provenance

Bithumb Agent is a modified distribution derived from the open-source
[Hermes Agent](https://github.com/NousResearch/hermes-agent) codebase by Nous
Research. The upstream code is licensed under the MIT License.

The complete upstream MIT license text and its original copyright notice are
preserved without replacement in [LICENSE](LICENSE):

```text
Copyright (c) 2025 Nous Research
```

The package metadata and Bithumb-specific source headers identify that license
with the SPDX short identifier `MIT`.

The Bithumb-specific modifications in this repository are distributed under
the same MIT License. The original copyright remains with its original owner;
the customization notice identifies the maintainers of the modifications and
does not transfer or erase upstream ownership.

## 2. How Hermes Agent was changed into Bithumb Agent

The customization consists of the following reviewed changes:

1. **Distribution and command name**
   - Renamed the published Python package and console command to
     `bithumb-agent`.
   - Added a Bithumb-specific entry point that applies the restricted runtime
     policy before loading the inherited CLI implementation.

2. **CLI identity and onboarding**
   - Replaced the initial user-facing identity with Bithumb Agent naming,
     orange terminal colors, and the `OPEN-SOURCE CUSTOMIZATION` notice.
   - Added `/bit gpt`, `/bit gemini`, `/bit status`, and `/bit help` onboarding
     commands.

3. **Authentication and model access**
   - Restricted the supported user-facing providers to ChatGPT/Codex OAuth and
     Google Antigravity OAuth.
   - Added a standalone ChatGPT/Codex browser OAuth flow using PKCE, a
     loopback-only callback, and OAuth state validation.
   - Reuses valid Bithumb Agent or official Codex credentials when available;
     Device Code authentication is retained only for remote/headless use.
   - API-key and arbitrary custom inference endpoint onboarding is rejected at
     the Bithumb Agent boundary.

4. **Reduced execution surface**
   - Limited exposed agent tools to terminal/process, local file operations,
     local code execution, todo, and clarification functions.
   - Disabled plugins, MCP servers, web/browser automation, media generation,
     messaging, cron, delegation, computer control, shell hooks, and approval
     bypass modes in the Bithumb Agent command and runtime policy.
   - Excluded the removed managed gateway and skill-tool modules from the
     published distribution.

5. **Packaging and compatibility**
   - Added the `bithumb-agent` Python package metadata and console entry point.
   - Declared and pinned runtime dependencies, included the license/notice
     documents in built distributions, and verified Python 3.14 installation.
   - Added regression tests for branding, provider restrictions, tool-policy
     enforcement, removed-module packaging, OAuth callback security, and
     standalone startup.

## 3. Inherited code and internal names

This remains a derivative work, not a clean-room rewrite. Some internal Python
module names, compatibility fields, comments, and dormant upstream source files
still use `hermes` terminology so that the inherited implementation remains
reviewable and compatible. Those internal names do not change the distributed
product name, which is Bithumb Agent.

Some dormant upstream files remain in the source repository for maintenance and
comparison but are blocked by the Bithumb Agent runtime policy. The published
wheel is additionally audited to exclude the specifically removed managed
gateway and skill-tool modules. See [SECURITY_REVIEW.md](SECURITY_REVIEW.md) for
the security boundary; this document records provenance and modifications, not
a claim that every inherited source file was rewritten.

## 4. Google Antigravity clarification

The CLI experience and Gemini login integration are inspired by and interoperate
with Google Antigravity. Google Antigravity source code is not claimed as part
of this repository. When used, its separately installed executable and its own
terms and licenses apply.

## 5. Trademarks and project status

This repository is an independent open-source customization and is not an
official Bithumb product or official distribution. Bithumb, Hermes Agent, Nous
Research, Google, Antigravity, OpenAI, ChatGPT, Codex, and other names and marks
belong to their respective owners.

Customization contact: `ilhong.kim@bithumbcorp.com`

## 6. Redistribution checklist

Anyone redistributing copies or substantial portions of Bithumb Agent should:

- keep [LICENSE](LICENSE), including the Nous Research copyright notice and
  the complete MIT permission/warranty text;
- keep [NOTICE.md](NOTICE.md) and this customization record with the source or
  binary distribution;
- avoid representing this independent customization as an official product of
  Bithumb, Nous Research, Google, or OpenAI; and
- review licenses for separately installed dependencies and external tools.

This record is informational and is not a replacement for the MIT License or
legal advice.
