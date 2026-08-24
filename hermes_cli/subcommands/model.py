"""``hermes model`` subcommand parser.

Extracted verbatim from ``hermes_cli/main.py:main()`` (god-file Phase 2).
Handler injected to avoid importing ``main``.
"""

from __future__ import annotations

from typing import Callable


def build_model_parser(subparsers, *, cmd_model: Callable) -> None:
    """Attach the ``model`` subcommand to ``subparsers``."""
    # =========================================================================
    # model command
    # =========================================================================
    model_parser = subparsers.add_parser(
        "model",
        help="Select ChatGPT OAuth or Gemini via Antigravity OAuth",
        description="Select one of Bithumb Agent' two API-keyless OAuth coding runtimes",
    )
    model_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh the ChatGPT OAuth model catalog.",
    )
    model_parser.set_defaults(func=cmd_model)
