"""``hermes auth`` subcommand parser.

Extracted verbatim from ``hermes_cli/main.py:main()`` (god-file Phase 2).
Handler injected to avoid importing ``main``.
"""

from __future__ import annotations

from typing import Callable


def build_auth_parser(subparsers, *, cmd_auth: Callable) -> None:
    """Attach the ``auth`` subcommand to ``subparsers``."""
    auth_parser = subparsers.add_parser(
        "auth",
        help="Manage ChatGPT and Gemini OAuth login",
    )
    auth_subparsers = auth_parser.add_subparsers(dest="auth_action")
    auth_add = auth_subparsers.add_parser("add", help="Connect an OAuth login")
    auth_add.add_argument(
        "provider",
        choices=["openai-codex", "antigravity-cli", "chatgpt", "gemini"],
        help="OAuth provider: openai-codex or antigravity-cli",
    )
    auth_add.add_argument("--label", help="Optional display label")
    auth_list = auth_subparsers.add_parser("list", help="List OAuth login status")
    auth_list.add_argument(
        "provider",
        nargs="?",
        choices=["openai-codex", "antigravity-cli", "chatgpt", "gemini"],
        help="Optional OAuth provider filter",
    )
    auth_remove = auth_subparsers.add_parser(
        "remove", help="Remove a pooled credential by index, id, or label"
    )
    auth_remove.add_argument("provider", choices=["openai-codex", "chatgpt"], help="ChatGPT OAuth provider")
    auth_remove.add_argument(
        "target", help="Credential index, entry id, or exact label"
    )
    auth_reset = auth_subparsers.add_parser(
        "reset", help="Clear exhaustion status for all credentials for a provider"
    )
    auth_reset.add_argument("provider", choices=["openai-codex", "chatgpt"], help="ChatGPT OAuth provider")
    auth_status = auth_subparsers.add_parser(
        "status", help="Show auth status for a provider"
    )
    auth_status.add_argument(
        "provider",
        choices=["openai-codex", "antigravity-cli", "chatgpt", "gemini"],
        help="OAuth provider",
    )
    auth_logout = auth_subparsers.add_parser(
        "logout", help="Log out a provider and clear stored auth state"
    )
    auth_logout.add_argument(
        "provider",
        choices=["openai-codex", "antigravity-cli", "chatgpt", "gemini"],
        help="OAuth provider",
    )
    auth_parser.set_defaults(func=cmd_auth)
