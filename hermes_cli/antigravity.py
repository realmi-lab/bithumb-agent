"""Shared helpers for Bithumb Agent' official Antigravity CLI integration.

Antigravity owns the Google OAuth session in the operating-system keyring.
Bithumb Agent never reads that token.  This module only resolves the official
``agy`` executable, strips alternate paid credential and proxy routes from
child processes, and keeps telemetry, updates, and AI-credit overages disabled.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tools.environments.local import hermes_subprocess_env


ANTIGRAVITY_PROVIDER_ID = "antigravity-cli"
ANTIGRAVITY_MARKER_BASE_URL = "antigravity-cli://local"
_SETTINGS_ENV = "BITHUMB_AGENT_ANTIGRAVITY_SETTINGS_PATH"


def resolve_antigravity_command() -> str:
    return (
        os.getenv("BITHUMB_AGENT_ANTIGRAVITY_CLI_COMMAND", "").strip()
        or os.getenv("ANTIGRAVITY_CLI_PATH", "").strip()
        or "agy"
    )


def resolve_antigravity_args() -> list[str]:
    raw = os.getenv("BITHUMB_AGENT_ANTIGRAVITY_CLI_ARGS", "").strip()
    return shlex.split(raw) if raw else []


def resolve_antigravity_executable(command: str | None = None) -> str | None:
    candidate = command or resolve_antigravity_command()
    resolved = shutil.which(candidate)
    if resolved:
        return resolved
    if candidate == "agy":
        official_path = Path.home() / ".local" / "bin" / "agy"
        if official_path.is_file() and os.access(official_path, os.X_OK):
            return str(official_path)
    return None


def antigravity_settings_path() -> Path:
    override = os.getenv(_SETTINGS_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".gemini" / "antigravity-cli" / "settings.json"


def load_antigravity_settings() -> dict[str, Any]:
    path = antigravity_settings_path()
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw) if raw.strip() else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Could not safely read Antigravity settings at {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Antigravity settings at {path} must contain a JSON object.")
    return payload


def enforce_oauth_without_credit_overages() -> Path:
    """Force account OAuth and disable telemetry and paid-credit fallback.

    ``modelProvider=gemini`` switches Antigravity to a Gemini API key, so it
    is removed. ``useG1Credits=false`` makes the CLI stop when baseline quota
    is exhausted instead of consuming purchased or promotional AI credits.
    Shell commands use Antigravity's terminal sandbox rather than the unsafe
    all-permissions bypass. Existing unrelated preferences are preserved.
    """

    path = antigravity_settings_path()
    settings = load_antigravity_settings()
    settings.pop("modelProvider", None)
    settings["useG1Credits"] = False
    settings["enableTelemetry"] = False
    settings["allowNonWorkspaceAccess"] = False
    settings["showFeedbackSurvey"] = False
    settings["showTips"] = False
    settings["enableTerminalSandbox"] = True
    settings["toolPermission"] = "proceed-in-sandbox"
    permissions = settings.get("permissions")
    if not isinstance(permissions, dict):
        permissions = {}
    existing_deny = permissions.get("deny")
    deny = (
        {str(rule) for rule in existing_deny if isinstance(rule, str)}
        if isinstance(existing_deny, list)
        else set()
    )
    # Antigravity is the Gemini inference/coding subprocess, not an egress or
    # extension bridge.  Its local file/terminal tools remain available for
    # coding, while URL browsing and MCP calls are denied at its own policy
    # boundary as well as being absent from Bithumb Agent' outer tool registry.
    deny.update({"read_url(*)", "execute_url(*)", "mcp(*)"})
    permissions["deny"] = sorted(deny)
    settings["permissions"] = permissions
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".settings.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(settings, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_name = handle.name
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
        os.chmod(path, 0o600)
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
    return path


def credit_overages_are_disabled() -> bool:
    try:
        settings = load_antigravity_settings()
    except RuntimeError:
        return False
    # Antigravity 1.1.19 omits the false/default value when it rewrites the
    # settings file. Only an explicit true enables credit fallback.
    return settings.get("useG1Credits", False) is False and "modelProvider" not in settings


def antigravity_subprocess_env() -> dict[str, str]:
    """Build an environment without API-key, Vertex, proxy, or updater routes."""

    env = hermes_subprocess_env(inherit_credentials=False)
    for key in (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_GEMINI_BASE_URL",
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "VERTEX_PROJECT_ID",
        "VERTEX_REGION",
        "VERTEX_CREDENTIALS_PATH",
        # Do not let a per-user shell setting silently bridge OAuth/model
        # traffic through an arbitrary process.  A bank-managed transparent
        # network proxy remains an infrastructure concern outside Bithumb Agent.
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "no_proxy",
    ):
        env.pop(key, None)
    # Official Antigravity CLI opt-out.  This prevents its background updater
    # from contacting the Cloud Run updater service or replacing the binary.
    env["AGY_CLI_DISABLE_AUTO_UPDATE"] = "true"
    # Antigravity 1.1.x initializes its browser driver even for non-browser
    # print-mode requests.  Pointing the documented driver override at the OS
    # null device makes that optional subsystem fail locally instead of trying
    # the Playwright Azure CDN mirrors.  The skip flag and loopback-only
    # download host are a second, fail-closed boundary: even if a future CLI
    # build ignores the driver override, it cannot fall back to an external
    # Playwright CDN through Bithumb Agent. Browser URL actions are also denied in
    # settings above, so there is no functional browser route to recover.
    env["PLAYWRIGHT_DRIVER_PATH"] = os.devnull
    env["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"
    env["PLAYWRIGHT_DOWNLOAD_HOST"] = "http://127.0.0.1:9/bithumb_agent-disabled"
    return env


def probe_antigravity_login(
    command: str | None = None,
    args: list[str] | None = None,
    *,
    timeout: float = 20.0,
) -> tuple[bool, str]:
    """Check cached OAuth using the quota command, which spends no model quota."""

    executable = resolve_antigravity_executable(command)
    if not executable:
        return False, "Antigravity CLI is not installed"
    try:
        completed = subprocess.run(
            [
                executable,
                *(args if args is not None else resolve_antigravity_args()),
                "-p",
                "/usage",
                "--output-format",
                "json",
                "--print-timeout",
                f"{max(1, int(timeout))}s",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 5,
            env=antigravity_subprocess_env(),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if completed.returncode == 0:
        return True, ""
    detail = (completed.stderr or completed.stdout or "authentication required").strip()
    return False, detail
