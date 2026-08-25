# SPDX-License-Identifier: MIT
# Derived from Hermes Agent (Copyright (c) 2025 Nous Research) and customized
# for the independent Bithumb Agent distribution. See LICENSE and NOTICE.md.

"""Security-first console entry point for Bithumb Agent.

The generated console shim imports this tiny module before the upstream CLI.
That ordering matters: configuration initialization otherwise creates disabled
Hermes directories and can start catalog work before ``main()`` gets a chance
to apply the Bithumb Agent policy.
"""

from __future__ import annotations

import sys
from typing import Any

from hermes_cli.bithumb_agent_policy import (
    apply_runtime_lockdown,
    extract_cli_command,
    validate_cli_argv,
)


_HELP = """\
Bithumb Agent - OAuth-only local coding agent

Usage:
  bithumb-agent                         Start interactive chat
  bithumb-agent chat -q \"질문\"          Run one chat request
  bithumb-agent auth ...                Manage ChatGPT/Google OAuth
  bithumb-agent model                   Select an OAuth model
  bithumb-agent status                  Show connection status
  bithumb-agent config ...              View or edit configuration
  bithumb-agent sessions ...            Manage local sessions
  bithumb-agent security ...            Run a local security audit
  bithumb-agent checkpoints ...         Manage local file checkpoints
  bithumb-agent logs ...                Inspect local logs
  bithumb-agent prompt-size             Inspect prompt size
  bithumb-agent completion [shell]      Generate shell completion
  bithumb-agent version                 Show version

Only terminal, file, local code execution, todo, clarification, and six
package-local read-only coding skills are available. Plugins, MCP, browser/web,
media, messaging, cron, delegation, dynamic skills, computer control, shell
hooks, and approval-bypass modes are disabled.
"""


def main() -> Any:
    apply_runtime_lockdown()
    if len(sys.argv) == 2 and sys.argv[1] in {"-h", "--help", "help"}:
        print(_HELP)
        return 0

    error = validate_cli_argv(sys.argv[1:])
    if error:
        print(error, file=sys.stderr)
        return 2

    # The upstream status screen enumerates disabled API-key providers,
    # gateways, MCP, and other integrations.  It also probes Antigravity by
    # launching a subprocess, which can hang or reopen its Google login UI.
    # Bithumb Agent exposes a two-provider, read-only status instead.
    if extract_cli_command(sys.argv[1:]) == "status":
        from hermes_cli.bithumb_onboarding import show_bit_status

        show_bit_status()
        return 0

    from hermes_cli.main import main as upstream_main

    return upstream_main()


if __name__ == "__main__":
    raise SystemExit(main() or 0)
