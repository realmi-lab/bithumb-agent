# SPDX-License-Identifier: MIT
# Derived from Hermes Agent (Copyright (c) 2025 Nous Research) and customized
# for the independent Bithumb Agent distribution. See LICENSE and NOTICE.md.

"""Bithumb Agent's locked-down OAuth and local-tool policy.

The upstream Hermes source supports many inference backends and integrations.
Bithumb Agent deliberately exposes and executes only two subscription-backed login
paths:

* ``openai-codex`` — ChatGPT/Codex OAuth handled by Hermes.
* ``antigravity-cli`` — Google OAuth handled by the official Antigravity CLI.

No API key, custom endpoint, plugin, MCP server, shell hook, background update
check, or non-coding tool is accepted at the Bithumb Agent runtime boundary.
"""

from __future__ import annotations

import os
from typing import Iterable, Optional


ALLOWED_PROVIDERS: tuple[str, str] = ("openai-codex", "antigravity-cli")
ALLOWED_PROVIDER_SET = frozenset(ALLOWED_PROVIDERS)

# Keep this list intentionally small.  These are the only toolsets and tool
# handlers that a Bithumb Agent model may see or invoke.  Terminal commands retain
# Hermes' normal approval/sandbox controls; unrelated network-capable tools
# such as web search, browser automation, TTS, image generation, messaging,
# cron, delegation, skills, memory, and computer use are excluded.
ALLOWED_TOOLSETS: tuple[str, ...] = (
    "terminal",
    "file",
    "code_execution",
    "todo",
    "clarify",
)
ALLOWED_TOOLSET_SET = frozenset(ALLOWED_TOOLSETS)
ALLOWED_TOOL_NAMES = frozenset(
    {
        "terminal",
        "process",
        "read_file",
        "write_file",
        "patch",
        "search_files",
        "execute_code",
        "todo",
        "clarify",
    }
)
ALLOWED_BUILTIN_TOOL_MODULES = frozenset(
    {
        "tools.terminal_tool",
        "tools.process_registry",
        "tools.file_tools",
        "tools.code_execution_tool",
        "tools.todo_tool",
        "tools.clarify_tool",
    }
)

ALLOWED_CLI_COMMANDS = frozenset(
    {
        None,
        "chat",
        "model",
        "auth",
        "status",
        "config",
        "sessions",
        "security",
        "checkpoints",
        "version",
        "logs",
        "prompt-size",
        "completion",
    }
)

# These upstream switches widen execution beyond the reviewed coding surface.
# Reject them before importing the full upstream CLI so they cannot initialize
# plugins, skills, shell hooks, or approval-bypass state as a side effect.
FORBIDDEN_CLI_FLAGS = frozenset(
    {
        "-s",
        "--skills",
        "--accept-hooks",
        "--yolo",
        "-z",
        "--oneshot",
        "--tui",
        "--tui-dev",
    }
)

_CLI_VALUE_FLAGS = frozenset(
    {
        "-m",
        "--model",
        "--provider",
        "-t",
        "--toolsets",
        "-r",
        "--resume",
        "-c",
        "--continue",
        "--usage-file",
        "-p",
        "--profile",
    }
)


def apply_runtime_lockdown() -> None:
    """Apply Bithumb Agent's non-optional local integration lockdown.

    ``HERMES_SAFE_MODE`` disables Python plugins, MCP discovery, and shell
    hooks without ignoring the user's selected OAuth provider or workspace.
    The Bithumb Agent-specific update flag is consumed by the banner/update prefetch
    path and is also forwarded to Antigravity as its vendor-supported update
    opt-out.
    """

    os.environ["HERMES_SAFE_MODE"] = "1"
    os.environ["HERMES_ENABLE_PROJECT_PLUGINS"] = "0"
    os.environ["HERMES_IGNORE_RULES"] = "1"
    os.environ["BITHUMB_AGENT_DISABLE_AUTO_UPDATE"] = "1"


def restrict_toolsets(requested: Optional[Iterable[str]]) -> list[str]:
    """Return only the coding toolsets allowed by the Bithumb Agent policy.

    ``None`` means the caller requested its default set, which is the complete
    Bithumb Agent coding allow-list rather than Hermes' upstream all-tools default.
    Explicit requests can only narrow this list, never widen it.
    """

    if requested is None:
        return list(ALLOWED_TOOLSETS)
    requested_set = {str(name) for name in requested}
    return [name for name in ALLOWED_TOOLSETS if name in requested_set]


def tool_is_allowed(name: str) -> bool:
    """Return whether a runtime tool dispatch is permitted by Bithumb Agent."""

    return str(name) in ALLOWED_TOOL_NAMES


def cli_command_is_allowed(name: Optional[str]) -> bool:
    """Return whether a top-level CLI command belongs to the coding surface."""

    return name in ALLOWED_CLI_COMMANDS


def extract_cli_command(argv: Iterable[str]) -> Optional[str]:
    """Return the first top-level command after reviewed global options."""

    items = [str(value) for value in argv]
    index = 0
    while index < len(items):
        item = items[index]
        if item == "--":
            return items[index + 1] if index + 1 < len(items) else None
        if item.startswith("-"):
            if "=" not in item and item in _CLI_VALUE_FLAGS and index + 1 < len(items):
                index += 2
            else:
                index += 1
            continue
        return item
    return None


def validate_cli_argv(argv: Iterable[str]) -> Optional[str]:
    """Return a fail-closed error for a forbidden flag or command.

    This lightweight check runs in the console entry module before the large
    upstream command graph is imported.  It is intentionally conservative:
    Bithumb Agent accepts prompts through ``chat -q`` or the interactive
    prompt, not as unknown top-level command names.
    """

    items = [str(value) for value in argv]
    for item in items:
        flag = item.split("=", 1)[0]
        if flag in FORBIDDEN_CLI_FLAGS or (
            len(flag) > 2 and flag[:2] in {"-s", "-z"}
        ):
            return f"Option {flag!r} is disabled by the Bithumb Agent coding-only security policy."

    command = extract_cli_command(items)

    if command == "help":
        return None
    if not cli_command_is_allowed(command):
        return f"Command {command!r} is disabled by the Bithumb Agent coding-only security policy."
    return None


def integration_startup_is_allowed() -> bool:
    """Whether plugin, MCP, and shell-hook startup may run.

    The answer is deliberately constant rather than configuration-driven so
    no user or project file can widen the distributed Bithumb Agent runtime.
    """

    return False

_ALIASES = {
    "chatgpt": "openai-codex",
    "chatgpt-oauth": "openai-codex",
    "codex": "openai-codex",
    "openai": "openai-codex",
    "openai-codex": "openai-codex",
    "gemini": "antigravity-cli",
    "gemini-oauth": "antigravity-cli",
    "google": "antigravity-cli",
    "google-gemini": "antigravity-cli",
    "antigravity": "antigravity-cli",
    "agy": "antigravity-cli",
    "antigravity-cli": "antigravity-cli",
    # Migrate the provider name used by the first local Bithumb Agent prototype.
    "gemini-cli": "antigravity-cli",
}


class BithumbAgentProviderError(ValueError):
    """Raised when a caller tries to bypass Bithumb Agent's OAuth-only policy."""


def normalize_provider(
    provider: Optional[str],
    *,
    allow_auto: bool = True,
) -> str:
    """Return a canonical Bithumb Agent provider or reject it.

    ``auto`` is retained only as a selection instruction; it never enables
    upstream Hermes' API-key environment-variable detection.
    """

    normalized = str(provider or "auto").strip().lower()
    if allow_auto and normalized in {"", "auto"}:
        return "auto"
    canonical = _ALIASES.get(normalized, normalized)
    if canonical not in ALLOWED_PROVIDER_SET:
        raise BithumbAgentProviderError(
            f"Bithumb Agent only supports ChatGPT OAuth (openai-codex) and "
            f"Gemini via Antigravity OAuth (antigravity-cli); provider "
            f"{normalized!r} is disabled."
        )
    return canonical


def reject_api_credentials(
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> None:
    """Reject API-key/custom-endpoint escape hatches."""

    if str(api_key or "").strip() or str(base_url or "").strip():
        raise BithumbAgentProviderError(
            "Bithumb Agent is OAuth-only: API keys and custom inference endpoints are disabled."
        )
