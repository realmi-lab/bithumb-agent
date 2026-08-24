# Bithumb Agent security-review status

Reviewed: 2026-08-24 (Asia/Seoul)

## Executive verdict

The current runtime is locked to coding tools and two OAuth-backed model paths,
but the repository is **not yet eligible for a strict “unrelated code must not
exist” approval**. Runtime controls and source-minimality are separate review
requirements:

- Runtime control: **pass with documented residuals**.
- Source tree contains dormant upstream providers, gateways, plugins, browser,
  messaging, update, and web-server implementations: **fail**.
- Google Antigravity CLI is an external compiled dependency that contains its
  own browser, MCP, plugin, skill, subagent, and updater implementations:
  **vendor-binary exception required, or Gemini must be removed**.

This document deliberately does not describe the application as bank-approved.

## Enforced runtime boundary

Model providers:

- `openai-codex`: ChatGPT/Codex subscription OAuth only.
- `antigravity-cli`: Google OAuth owned by the official `agy` executable.
- API keys, Vertex credentials, custom inference URLs, and fallback providers
  are rejected or stripped at the runtime boundary.

Local tools visible to or callable by the outer Bithumb Agent agent:

- `terminal`, `process`
- `read_file`, `write_file`, `patch`, `search_files`
- `execute_code`
- `todo`, `clarify`

The tool registry imports only the five reviewed coding modules plus the local
process registry. A direct dispatch of another registered name is denied before
plugin hooks, middleware, bridge handling, or execution.

Disabled startup surfaces:

- Python plugin discovery
- project and entry-point plugins
- MCP server discovery
- shell hooks
- background version/update checks
- bundled skills at model runtime
- web search, browser automation, vision, image/video generation, TTS, memory,
  session search, delegation, cron, computer use, smart-home, music, and
  messaging toolsets

`~/.hermes/config.yaml` is an explicit allow-list and contains `no_mcp`, an
empty plugin allow-list, and an empty MCP map.

## Antigravity subprocess controls

Before every `agy` invocation, Bithumb Agent:

- removes Gemini API-key, Google ADC/Vertex, custom Gemini URL, and project
  credential environment variables;
- removes process-level HTTP, HTTPS, SOCKS, and bypass proxy variables;
- sets `AGY_CLI_DISABLE_AUTO_UPDATE=true`;
- sets `PLAYWRIGHT_DRIVER_PATH` to the operating-system null device, enables
  `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD`, and pins `PLAYWRIGHT_DOWNLOAD_HOST` to a
  closed loopback port so optional
  browser initialization fails locally and does not download Playwright;
- forces telemetry off, terminal sandboxing on, and non-workspace access off;
- denies `read_url(*)`, `execute_url(*)`, and `mcp(*)` in Antigravity's own
  permissions;
- launches print mode with `--sandbox` and `--disable-slash-commands`;
- never passes `--dangerously-skip-permissions`;
- disables paid AI-credit overage fallback.

Antigravity uses sparse settings persistence and may remove default-valued
fields when it exits. Bithumb Agent rewrites the enforced values immediately before
every invocation; the checked-in tests verify the child-process environment
and pre-launch settings.

Pinned dependency observed during review:

- `agy` version: `1.1.19`
- SHA-256: `96fae3fccfb444c7fb2c6d8d70426e5c978e4f21cfc4507a541f612a8b8ffeef`

## Network map

Required model/authentication destinations:

| Path | Destination | Purpose |
|---|---|---|
| ChatGPT | `auth.openai.com` | OAuth token issuance/refresh |
| ChatGPT | `chatgpt.com/backend-api/codex` | model list, usage, and responses |
| Gemini | `daily-cloudcode-pa.googleapis.com/v1internal:*` | model list, quota, and generation |
| Gemini login/support | Google-owned OAuth/profile/feature endpoints | login, profile, entitlement, and CLI feature configuration |

The latest hardened no-quota `/usage` probe logged only
`daily-cloudcode-pa.googleapis.com` as a remote HTTP destination. Previous
unhardened observation also found Google authentication/profile endpoints.

Explicitly blocked or disabled destinations/surfaces:

- Antigravity Cloud Run auto-updater
- Playwright Azure/Akamai/Verizon CDN mirrors
- arbitrary environment-configured proxy bridges
- Nous Portal/inference/tool gateway
- OpenRouter and other upstream model providers
- Bing Edge TTS and all image/video/web-search providers
- messaging gateways, remote MCP servers, and imported plugins

The dashboard, when used, listens only on `127.0.0.1:9119`.

## Residual risks requiring an approval decision

1. **External Antigravity binary.** It still contains browser, MCP, plugin,
   skill, updater, and subagent code even though Bithumb Agent disables those paths.
   A policy that forbids dormant capability code cannot approve this binary.
2. **Upstream source tree.** The checkout still includes many unrelated Hermes
   modules and hard-coded third-party endpoints. Runtime deny-lists do not make
   those source files disappear from a source review.
3. **Terminal egress.** Vibe coding requires a terminal. An approved terminal
   command can intentionally run package managers, Git, `curl`, or arbitrary
   programs. Enforce destination control at the bank's host/network layer and
   retain command approvals; application code alone cannot prove zero egress
   for a general-purpose shell.
4. **Prompt and source disclosure.** Both approved model paths necessarily send
   user prompts and selected source/context to their model vendor. Data
   classification, DLP, retention, and contractual approval remain external
   governance requirements.

## Approval paths

For a strict source-minimal build, create a clean distribution repository that
contains only the two adapters and reviewed local coding modules. If dormant
code is prohibited even in vendor dependencies, omit Gemini/`agy` and ship a
ChatGPT-only build.

If Gemini is mandatory, treat `agy` as a pinned vendor dependency: approve the
hash above, prohibit self-update, enforce OS/network egress allow-lists, record
the vendor exception, and repeat the network trace after every reviewed binary
upgrade.
