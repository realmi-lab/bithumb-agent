"""OpenAI-compatible facade for the official Google Antigravity CLI.

The CLI owns and refreshes its Google OAuth session. Bithumb Agent invokes the
official headless JSON interface and never reads or copies OAuth tokens.
Paid AI-credit overages and alternate API-key/Vertex credential paths are
disabled before every invocation.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from hermes_cli.antigravity import (
    ANTIGRAVITY_MARKER_BASE_URL,
    antigravity_subprocess_env,
    enforce_oauth_without_credit_overages,
    resolve_antigravity_args,
    resolve_antigravity_command,
    resolve_antigravity_executable,
)


_DEFAULT_TIMEOUT_SECONDS = 900.0


def _render_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(part.strip() for part in parts if part.strip())
    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text.strip()
        return json.dumps(content, ensure_ascii=False)
    return str(content).strip()


def _format_prompt(messages: list[dict[str, Any]]) -> str:
    transcript: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = _render_content(message.get("content"))
        if not content:
            continue
        role = str(message.get("role") or "context").strip().lower()
        label = {
            "system": "System",
            "user": "User",
            "assistant": "Assistant",
            "tool": "Tool result",
        }.get(role, "Context")
        transcript.append(f"{label}:\n{content}")

    return "\n\n".join(
        [
            "You are the active coding agent for Bithumb Agent.",
            "Work directly in the current project directory. Inspect files, edit code, and run checks when allowed and relevant. Follow the system instructions and prior conversation below. At the end, give a concise summary of completed work.",
            "Conversation:\n\n" + "\n\n".join(transcript),
            "Continue from the latest user request now.",
        ]
    )


def _effective_timeout(timeout: Any) -> float:
    if timeout is None:
        return _DEFAULT_TIMEOUT_SECONDS
    if isinstance(timeout, (int, float)):
        return float(timeout)
    candidates = [
        getattr(timeout, attr, None)
        for attr in ("read", "write", "connect", "pool", "timeout")
    ]
    numeric = [float(value) for value in candidates if isinstance(value, (int, float))]
    return max(numeric) if numeric else _DEFAULT_TIMEOUT_SECONDS


def _usage_from_payload(payload: dict[str, Any]) -> SimpleNamespace:
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    prompt_tokens = int(usage.get("input_tokens") or 0)
    completion_tokens = int(usage.get("output_tokens") or 0)
    cached_tokens = int(usage.get("cache_read_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
    return SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        prompt_tokens_details=SimpleNamespace(cached_tokens=cached_tokens),
    )


def _friendly_error(detail: str) -> str:
    lowered = detail.lower()
    if "authentication required" in lowered or "sign in" in lowered or "login" in lowered:
        return detail + "\nRun `bithumb-agent auth add antigravity-cli` to sign in with Google."
    if any(token in lowered for token in ("quota", "weekly limit", "baseline", "rate limit")):
        return (
            detail
            + "\nAntigravity baseline quota is exhausted. Bithumb Agent will not use paid "
            "AI-credit overages; wait for the quota to refresh."
        )
    return detail


class _AntigravityChatCompletions:
    def __init__(self, client: "AntigravityCLIClient"):
        self._client = client

    def create(self, **kwargs: Any) -> Any:
        return self._client._create_chat_completion(**kwargs)


class _AntigravityChatNamespace:
    def __init__(self, client: "AntigravityCLIClient"):
        self.completions = _AntigravityChatCompletions(client)


class AntigravityCLIClient:
    """Minimal OpenAI-client-compatible wrapper around official ``agy``."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        antigravity_cwd: str | None = None,
        **_: Any,
    ):
        del api_key
        self.base_url = base_url or ANTIGRAVITY_MARKER_BASE_URL
        self._command = command or resolve_antigravity_command()
        self._extra_args = list(args) if args is not None else resolve_antigravity_args()
        self._cwd = str(Path(antigravity_cwd or os.getcwd()).resolve())
        self.chat = _AntigravityChatNamespace(self)
        self.is_closed = False
        self._active_process: subprocess.Popen[str] | None = None
        self._process_lock = threading.Lock()

    def close(self) -> None:
        with self._process_lock:
            process = self._active_process
            self._active_process = None
        self.is_closed = True
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            process.kill()

    def _create_chat_completion(
        self,
        *,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        timeout: Any = None,
        stream: bool = False,
        **_: Any,
    ) -> Any:
        enforce_oauth_without_credit_overages()
        executable = resolve_antigravity_executable(self._command)
        if not executable:
            raise RuntimeError(
                "Antigravity CLI was not found. Install the official `agy` CLI, then "
                "run `bithumb-agent auth add antigravity-cli`."
            )

        prompt = _format_prompt(messages or [])
        effective_timeout = _effective_timeout(timeout)
        command = [
            executable,
            *self._extra_args,
            "--disable-slash-commands",
            "--sandbox",
            "--output-format",
            "json",
            "--print-timeout",
            f"{max(1, int(effective_timeout))}s",
        ]
        if model and model.strip().lower() not in {"auto", "antigravity-cli"}:
            command.extend(["--model", model.strip()])
        command.extend(["-p", prompt])

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._cwd,
                env=antigravity_subprocess_env(),
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Antigravity CLI executable disappeared before launch.") from exc

        self.is_closed = False
        with self._process_lock:
            self._active_process = process
        try:
            stdout, stderr = process.communicate(timeout=effective_timeout + 5)
        except subprocess.TimeoutExpired as exc:
            self.close()
            raise TimeoutError("Timed out waiting for Antigravity CLI.") from exc
        finally:
            with self._process_lock:
                if self._active_process is process:
                    self._active_process = None

        if process.returncode != 0:
            detail = (stderr or stdout or "unknown Antigravity CLI error").strip()
            raise RuntimeError(
                f"Antigravity CLI failed (exit {process.returncode}): {_friendly_error(detail)}"
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Antigravity CLI returned invalid JSON output.") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Antigravity CLI returned an unexpected JSON response.")
        status = str(payload.get("status") or "").upper()
        if status != "SUCCESS":
            detail = str(payload.get("error") or f"unexpected status {status or 'UNKNOWN'}")
            raise RuntimeError(f"Antigravity CLI error: {_friendly_error(detail)}")

        response_text = str(payload.get("response") or "").strip()
        usage = _usage_from_payload(payload)
        message = SimpleNamespace(
            content=response_text,
            tool_calls=[],
            reasoning=None,
            reasoning_content=None,
            reasoning_details=None,
        )
        completion = SimpleNamespace(
            choices=[SimpleNamespace(message=message, finish_reason="stop")],
            usage=usage,
            model=model or "auto",
        )
        if stream:
            delta = SimpleNamespace(
                role="assistant",
                content=response_text or None,
                tool_calls=None,
                reasoning_content=None,
                reasoning=None,
            )
            return [
                SimpleNamespace(
                    choices=[SimpleNamespace(index=0, delta=delta, finish_reason="stop")],
                    model=completion.model,
                    usage=None,
                ),
                SimpleNamespace(choices=[], model=completion.model, usage=usage),
            ]
        return completion


def antigravity_cli_available(command: str | None = None) -> bool:
    return resolve_antigravity_executable(command) is not None
