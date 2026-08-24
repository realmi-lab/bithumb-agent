from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agent.antigravity_cli_client import AntigravityCLIClient
from hermes_cli.bithumb_agent_policy import (
    ALLOWED_PROVIDERS,
    BithumbAgentProviderError,
    normalize_provider,
    reject_api_credentials,
)


def test_only_chatgpt_and_gemini_are_canonical_providers():
    from hermes_cli.models import CANONICAL_PROVIDERS, list_available_providers

    assert [entry.slug for entry in CANONICAL_PROVIDERS] == list(ALLOWED_PROVIDERS)
    assert [entry["id"] for entry in list_available_providers()] == list(ALLOWED_PROVIDERS)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("chatgpt", "openai-codex"),
        ("codex", "openai-codex"),
        ("gemini", "antigravity-cli"),
        ("google", "antigravity-cli"),
        ("agy", "antigravity-cli"),
        ("gemini-cli", "antigravity-cli"),
    ],
)
def test_oauth_provider_aliases(value, expected):
    assert normalize_provider(value) == expected


@pytest.mark.parametrize("value", ["openrouter", "anthropic", "openai-api", "custom"])
def test_other_providers_are_rejected(value):
    with pytest.raises(BithumbAgentProviderError, match="only supports"):
        normalize_provider(value)


def test_api_keys_and_custom_endpoints_are_rejected():
    with pytest.raises(BithumbAgentProviderError, match="OAuth-only"):
        reject_api_credentials(api_key="secret")
    with pytest.raises(BithumbAgentProviderError, match="OAuth-only"):
        reject_api_credentials(base_url="http://localhost:1234/v1")


def test_auth_resolver_never_falls_back_to_api_keys(monkeypatch):
    import hermes_cli.auth as auth

    monkeypatch.setenv("OPENAI_API_KEY", "must-not-be-used")
    monkeypatch.setenv("OPENROUTER_API_KEY", "must-not-be-used")
    with pytest.raises(auth.AuthError, match="API keys"):
        auth.resolve_provider("auto", explicit_api_key="must-not-be-used")
    with pytest.raises(auth.AuthError, match="only supports"):
        auth.resolve_provider("openrouter")


def test_antigravity_usage_is_not_reported_as_metered_api_cost():
    from agent.usage_pricing import resolve_billing_route

    route = resolve_billing_route("auto", provider="antigravity-cli")
    assert route.billing_mode == "subscription_included"


class _FakeProcess:
    def __init__(self, command, **kwargs):
        self.command = command
        self.kwargs = kwargs
        self.returncode = 0

    def communicate(self, timeout=None):
        del timeout
        payload = {
            "status": "SUCCESS",
            "response": "작업 완료",
            "usage": {
                "input_tokens": 12,
                "output_tokens": 5,
                "cache_read_tokens": 2,
                "total_tokens": 17,
            },
        }
        return json.dumps(payload), ""

    def poll(self):
        return self.returncode


def test_antigravity_adapter_uses_headless_json_and_disables_paid_routes(monkeypatch, tmp_path):
    captured = {}

    def fake_popen(command, **kwargs):
        process = _FakeProcess(command, **kwargs)
        captured["process"] = process
        return process

    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"modelProvider": "gemini", "theme": "dark", "useG1Credits": True}),
        encoding="utf-8",
    )
    monkeypatch.setenv("BITHUMB_AGENT_ANTIGRAVITY_SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr("agent.antigravity_cli_client.subprocess.Popen", fake_popen)
    monkeypatch.setattr(
        "agent.antigravity_cli_client.resolve_antigravity_executable",
        lambda command: command,
    )
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-forwarded")
    monkeypatch.setenv("GOOGLE_API_KEY", "must-not-be-forwarded")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/paid/vertex.json")
    monkeypatch.setenv("GOOGLE_GEMINI_BASE_URL", "https://paid.example")
    monkeypatch.setenv("HTTPS_PROXY", "http://unreviewed-proxy.example:8080")
    monkeypatch.setenv("ALL_PROXY", "socks5://unreviewed-proxy.example:1080")

    client = AntigravityCLIClient(command="agy", antigravity_cwd=str(tmp_path))
    result = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": "코드를 고쳐줘"}],
    )

    process = captured["process"]
    assert process.command[:1] == ["agy"]
    assert process.command[process.command.index("--output-format") + 1] == "json"
    assert "--disable-slash-commands" in process.command
    assert "--sandbox" in process.command
    assert "--dangerously-skip-permissions" not in process.command
    assert "--model" not in process.command
    assert "코드를 고쳐줘" in process.command[process.command.index("-p") + 1]
    assert "GEMINI_API_KEY" not in process.kwargs["env"]
    assert "GOOGLE_API_KEY" not in process.kwargs["env"]
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in process.kwargs["env"]
    assert "GOOGLE_GEMINI_BASE_URL" not in process.kwargs["env"]
    assert "HTTPS_PROXY" not in process.kwargs["env"]
    assert "ALL_PROXY" not in process.kwargs["env"]
    assert process.kwargs["env"]["AGY_CLI_DISABLE_AUTO_UPDATE"] == "true"
    assert process.kwargs["env"]["PLAYWRIGHT_DRIVER_PATH"]
    assert process.kwargs["env"]["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] == "1"
    assert process.kwargs["env"]["PLAYWRIGHT_DOWNLOAD_HOST"].startswith(
        "http://127.0.0.1:"
    )
    saved_settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert saved_settings["useG1Credits"] is False
    assert saved_settings["enableTelemetry"] is False
    assert "modelProvider" not in saved_settings
    assert saved_settings["enableTerminalSandbox"] is True
    assert saved_settings["allowNonWorkspaceAccess"] is False
    assert saved_settings["showFeedbackSurvey"] is False
    assert saved_settings["showTips"] is False
    assert saved_settings["toolPermission"] == "proceed-in-sandbox"
    assert saved_settings["permissions"]["deny"] == [
        "execute_url(*)",
        "mcp(*)",
        "read_url(*)",
    ]
    assert saved_settings["theme"] == "dark"
    assert result.choices[0].message.content == "작업 완료"
    assert result.usage.prompt_tokens == 12
    assert result.usage.completion_tokens == 5
    assert result.usage.prompt_tokens_details.cached_tokens == 2


def test_bithumb_agent_tool_policy_is_fail_closed():
    from hermes_cli.bithumb_agent_policy import (
        ALLOWED_TOOL_NAMES,
        ALLOWED_TOOLSETS,
        apply_runtime_lockdown,
    )

    apply_runtime_lockdown()

    import model_tools

    exposed = {
        entry["function"]["name"]
        for entry in model_tools.get_tool_definitions(quiet_mode=True)
    }
    assert exposed <= ALLOWED_TOOL_NAMES
    assert "web_search" not in exposed
    assert "browser_navigate" not in exposed
    assert "text_to_speech" not in exposed
    assert "delegate_task" not in exposed

    widened = {
        entry["function"]["name"]
        for entry in model_tools.get_tool_definitions(
            enabled_toolsets=["all", "web", "browser", *ALLOWED_TOOLSETS],
            quiet_mode=True,
        )
    }
    assert widened == exposed

    blocked = json.loads(model_tools.handle_function_call("web_search", {"query": "x"}))
    assert "disabled by Bithumb Agent security policy" in blocked["error"]


def test_antigravity_runtime_is_external_process_oauth(monkeypatch):
    import hermes_cli.config as config
    import hermes_cli.runtime_provider as runtime

    monkeypatch.setattr(config, "load_config", lambda: {})
    monkeypatch.setattr(runtime, "_get_model_config", lambda: {})
    monkeypatch.setattr(
        runtime,
        "resolve_external_process_provider_credentials",
        lambda provider: {
            "provider": provider,
            "api_key": "antigravity-cli",
            "base_url": "antigravity-cli://local",
            "command": "/usr/local/bin/agy",
            "args": [],
        },
    )

    resolved = runtime.resolve_runtime_provider(requested="gemini")
    assert resolved == {
        "provider": "antigravity-cli",
        "api_mode": "chat_completions",
        "base_url": "antigravity-cli://local",
        "api_key": "antigravity-cli",
        "command": "/usr/local/bin/agy",
        "args": [],
        "source": "google-oauth-via-antigravity-cli",
        "requested_provider": "antigravity-cli",
    }
