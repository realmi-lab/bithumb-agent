"""Security-first console entry point for Bithumb Agent.

The generated console shim imports this tiny module before the upstream CLI.
That ordering matters: configuration initialization otherwise creates disabled
Hermes directories and can start catalog work before ``main()`` gets a chance
to apply the Bithumb Agent policy.
"""

from __future__ import annotations

from typing import Any

from hermes_cli.bithumb_agent_policy import apply_runtime_lockdown


def main() -> Any:
    apply_runtime_lockdown()
    from hermes_cli.main import main as upstream_main

    return upstream_main()
