# SPDX-License-Identifier: MIT
"""Process-local write-origin tracking for Bithumb Agent.

The upstream conversation loop used ``tools.skill_provenance`` for this small
piece of state.  Skills are intentionally not distributed by Bithumb Agent,
so keeping that import made the first real chat turn fail on a clean install.
This module owns only the generic write-origin value needed by memory/write
approval code and has no skill loading, gateway, network, or plugin behavior.
"""

from __future__ import annotations

from contextvars import ContextVar, Token


_CURRENT_WRITE_ORIGIN: ContextVar[str] = ContextVar(
    "bithumb_agent_write_origin",
    default="foreground",
)


def set_current_write_origin(origin: str) -> Token[str]:
    """Bind the write origin for the current async/thread context."""

    return _CURRENT_WRITE_ORIGIN.set(str(origin or "foreground"))


def get_current_write_origin() -> str:
    """Return the current write origin without importing optional features."""

    return _CURRENT_WRITE_ORIGIN.get()
