from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen

import pytest

from agent.antigravity_cli_client import AntigravityCLIClient
from hermes_cli.bithumb_agent_policy import (
    ALLOWED_PROVIDERS,
    BithumbAgentProviderError,
    normalize_provider,
    reject_api_credentials,
    validate_cli_argv,
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
    assert {"skills_list", "skill_view"} <= exposed
    assert "skill_manage" not in exposed
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


def test_managed_tool_gateway_is_not_distributed():
    project_root = Path(__file__).resolve().parents[1]
    assert not (project_root / "tools" / "managed_tool_gateway.py").exists()

    from tools.tool_backend_helpers import managed_nous_tools_enabled

    assert managed_nous_tools_enabled() is False


@pytest.mark.parametrize("command", ["tools", "doctor", "dashboard", "gateway", "mcp", "cron"])
def test_integration_cli_commands_are_rejected_before_dispatch(command):
    error = validate_cli_argv([command, "--help"])
    assert error is not None
    assert "disabled by the Bithumb Agent" in error


@pytest.mark.parametrize(
    "argv",
    [
        ["--yolo"],
        ["--accept-hooks"],
        ["--skills", "anything"],
        ["-s", "anything"],
        ["--oneshot", "prompt"],
        ["-z", "prompt"],
        ["-zprompt"],
        ["--tui"],
        ["--tui-dev"],
    ],
)
def test_integration_and_approval_bypass_flags_are_rejected(argv):
    assert validate_cli_argv(argv) is not None


def test_reviewed_cli_commands_remain_available():
    for argv in (
        [],
        ["chat", "-q", "hello"],
        ["auth", "status", "openai-codex"],
        ["--provider", "openai-codex", "status"],
        ["--profile", "work", "sessions", "list"],
    ):
        assert validate_cli_argv(argv) is None


def test_status_command_is_detected_after_global_options():
    from hermes_cli.bithumb_agent_policy import extract_cli_command

    assert extract_cli_command(["status"]) == "status"
    assert extract_cli_command(["--provider", "openai-codex", "status"]) == "status"
    assert extract_cli_command(["--profile=work", "status"]) == "status"


def test_integration_startup_is_permanently_disabled():
    from hermes_cli.bithumb_agent_policy import integration_startup_is_allowed

    assert integration_startup_is_allowed() is False


def test_first_run_guidance_is_bithumb_oauth_only(tmp_path):
    environment = os.environ.copy()
    environment["HERMES_HOME"] = str(tmp_path / "isolated-home")
    for name in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
    ):
        environment.pop(name, None)

    result = subprocess.run(
        [sys.executable, "-m", "hermes_cli.bithumb_agent_entry", "chat", "-q", "test"],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 1
    assert "Bithumb Agent OAuth login is required" in output
    assert "bithumb-agent auth add openai-codex" in output
    assert "bithumb-agent auth add antigravity-cli" in output
    assert "OPENROUTER_API_KEY" not in output
    assert "custom endpoint" not in output.lower()
    assert "Hermes Setup" not in output


@pytest.mark.parametrize(
    ("command", "provider"),
    [
        ("/bit gpt", "openai-codex"),
        ("/bit gemini", "antigravity-cli"),
    ],
)
def test_bit_login_commands_dispatch_to_reviewed_oauth(command, provider):
    from hermes_cli.bithumb_onboarding import handle_bit_command

    connected = []
    output = []
    selected = handle_bit_command(
        command,
        emit=output.append,
        connector=lambda value: connected.append(value) or value,
    )

    assert selected == provider
    assert connected == [provider]
    assert any("로그인" in line for line in output)


def test_first_login_shell_starts_agent_after_bit_login():
    from hermes_cli.bithumb_onboarding import run_first_login_shell

    commands = iter(["hello", "/bit gpt"])
    output = []
    selected = run_first_login_shell(
        input_fn=lambda _prompt: next(commands),
        emit=output.append,
        connector=lambda provider: provider,
    )

    assert selected == "openai-codex"
    assert any("/bit gpt" in line for line in output)
    assert any("/bit gemini" in line for line in output)
    assert any("사용법" in line for line in output)


def test_bit_command_is_registered_for_help_and_completion():
    from hermes_cli.commands import resolve_command

    command = resolve_command("bit")
    assert command is not None
    assert command.subcommands == ("gpt", "gemini", "status", "help")


@pytest.mark.parametrize(
    ("provider", "expected_model"),
    [
        ("openai-codex", "gpt-account-default"),
        ("antigravity-cli", "auto"),
    ],
)
def test_bit_login_selects_provider_and_usable_default(
    monkeypatch, provider, expected_model
):
    import hermes_cli.auth as auth
    import hermes_cli.auth_commands as auth_commands
    import hermes_cli.codex_models as codex_models
    from hermes_cli.bithumb_onboarding import connect_bit_provider

    added = []
    selected = []
    monkeypatch.setattr(
        auth_commands,
        "auth_add_command",
        lambda args: added.append(args.provider),
    )
    monkeypatch.setattr(auth, "reuse_codex_login_if_available", lambda: False)
    monkeypatch.setattr(
        auth,
        "_update_config_for_provider",
        lambda chosen, base_url, model: selected.append((chosen, base_url, model)),
    )
    monkeypatch.setattr(
        auth,
        "get_codex_auth_status",
        lambda: {"api_key": "oauth-token"},
    )
    monkeypatch.setattr(
        codex_models,
        "get_codex_model_ids",
        lambda access_token=None: ["gpt-account-default"],
    )

    assert connect_bit_provider(provider) == provider
    assert added == [provider]
    assert selected[0][0] == provider
    assert selected[0][2] == expected_model


def test_codex_browser_authorize_url_matches_official_pkce_shape():
    import hermes_cli.auth as auth

    url = auth._codex_build_authorize_url(
        redirect_uri="http://localhost:1455/auth/callback",
        code_challenge="challenge-value",
        state="state-value",
    )
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.openai.com"
    assert parsed.path == "/oauth/authorize"
    assert query["client_id"] == [auth.CODEX_OAUTH_CLIENT_ID]
    assert query["redirect_uri"] == ["http://localhost:1455/auth/callback"]
    assert query["code_challenge"] == ["challenge-value"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == ["state-value"]
    assert query["scope"] == [auth.CODEX_OAUTH_SCOPE]
    assert query["id_token_add_organizations"] == ["true"]
    assert query["codex_cli_simplified_flow"] == ["true"]


def test_codex_callback_accepts_code_and_rejects_wrong_state():
    import hermes_cli.auth as auth

    handler, result = auth._make_codex_callback_handler(
        "/auth/callback", "expected-state"
    )
    server = auth.HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    port = server.server_address[1]
    with pytest.raises(HTTPError) as error:
        urlopen(
            f"http://127.0.0.1:{port}/auth/callback?code=secret&state=wrong",
            timeout=2,
        )
    thread.join(timeout=2)
    server.server_close()
    assert error.value.code == 400
    assert result["code"] is None
    assert result["error"] == "state_mismatch"

    handler, result = auth._make_codex_callback_handler(
        "/auth/callback", "expected-state"
    )
    server = auth.HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    port = server.server_address[1]
    with urlopen(
        f"http://127.0.0.1:{port}/auth/callback?code=secret&state=expected-state",
        timeout=2,
    ) as response:
        assert response.status == 200
    thread.join(timeout=2)
    server.server_close()
    assert result["code"] == "secret"
    assert result["error"] is None


def test_codex_browser_exchange_uses_pkce_and_keeps_tokens_private(monkeypatch):
    import hermes_cli.auth as auth

    captured = {}

    class Response:
        status_code = 200

        @staticmethod
        def json():
            return {
                "access_token": "access-secret",
                "refresh_token": "refresh-secret",
                "id_token": "id-secret",
            }

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    system_trust = object()
    monkeypatch.setattr(auth.httpx, "post", fake_post)
    monkeypatch.setattr(auth, "_resolve_verify", lambda: system_trust)
    creds = auth._codex_exchange_browser_code(
        code="authorization-secret",
        redirect_uri="http://localhost:1455/auth/callback",
        code_verifier="verifier-secret",
    )

    assert captured["url"] == auth.CODEX_OAUTH_TOKEN_URL
    assert captured["data"] == {
        "grant_type": "authorization_code",
        "code": "authorization-secret",
        "redirect_uri": "http://localhost:1455/auth/callback",
        "client_id": auth.CODEX_OAUTH_CLIENT_ID,
        "code_verifier": "verifier-secret",
    }
    assert captured["verify"] is system_trust
    assert creds["source"] == "loopback-pkce"
    assert creds["tokens"]["access_token"] == "access-secret"


def test_default_verify_uses_truststore_without_disabling_tls(monkeypatch):
    import ssl
    import sys
    from types import SimpleNamespace

    import hermes_cli.auth as auth

    system_context = object()

    def fake_ssl_context(protocol):
        assert protocol == ssl.PROTOCOL_TLS_CLIENT
        return system_context

    monkeypatch.setitem(
        sys.modules,
        "truststore",
        SimpleNamespace(SSLContext=fake_ssl_context),
    )

    assert auth._default_verify() is system_context


def test_explicit_ca_is_added_to_system_truststore(monkeypatch, tmp_path):
    import hermes_cli.auth as auth

    ca_bundle = tmp_path / "enterprise-root.pem"
    ca_bundle.write_text("test certificate placeholder", encoding="utf-8")

    class SystemContext:
        loaded_cafile = None

        def load_verify_locations(self, *, cafile):
            self.loaded_cafile = cafile

    context = SystemContext()
    monkeypatch.setattr(auth, "_default_verify", lambda: context)

    assert auth._resolve_verify(ca_bundle=str(ca_bundle)) is context
    assert context.loaded_cafile == str(ca_bundle)


def test_codex_browser_login_completes_through_local_callback(monkeypatch):
    import hermes_cli.auth as auth

    exchanged = {}

    def fake_open(authorize_url):
        query = parse_qs(urlparse(authorize_url).query)
        callback = (
            f'{query["redirect_uri"][0]}?code=browser-code&state={query["state"][0]}'
        )

        def send_callback():
            with urlopen(callback, timeout=2) as response:
                assert response.status == 200

        threading.Thread(target=send_callback, daemon=True).start()
        return True

    def fake_exchange(**kwargs):
        exchanged.update(kwargs)
        return {"source": "loopback-pkce", "tokens": {"access_token": "token"}}

    monkeypatch.setattr(auth.webbrowser, "open", fake_open)
    monkeypatch.setattr(auth, "_codex_exchange_browser_code", fake_exchange)
    creds = auth._codex_browser_login(timeout_seconds=3)

    assert creds["source"] == "loopback-pkce"
    assert exchanged["code"] == "browser-code"
    assert exchanged["redirect_uri"] in {
        "http://localhost:1455/auth/callback",
        "http://localhost:1457/auth/callback",
    }
    assert exchanged["code_verifier"]


def test_codex_login_uses_browser_locally_and_device_code_remotely(monkeypatch):
    import hermes_cli.auth as auth

    monkeypatch.setattr(auth, "_is_remote_session", lambda: False)
    monkeypatch.setattr(auth, "_can_open_graphical_browser", lambda: True)
    monkeypatch.setattr(auth, "_codex_browser_login", lambda: {"source": "browser"})
    monkeypatch.setattr(auth, "_codex_device_code_login", lambda: {"source": "device"})
    assert auth._codex_login_for_environment() == {"source": "browser"}

    monkeypatch.setattr(auth, "_is_remote_session", lambda: True)
    assert auth._codex_login_for_environment() == {"source": "device"}


def test_bit_gpt_reuses_official_codex_login_without_new_oauth(monkeypatch):
    import hermes_cli.auth as auth
    import hermes_cli.auth_commands as auth_commands
    from hermes_cli.bithumb_onboarding import connect_bit_provider

    added = []
    monkeypatch.setattr(auth, "reuse_codex_login_if_available", lambda: True)
    monkeypatch.setattr(auth_commands, "auth_add_command", lambda args: added.append(args))
    monkeypatch.setattr(auth, "_update_config_for_provider", lambda *args: None)
    monkeypatch.setattr(auth, "get_codex_auth_status", lambda: {"api_key": "token"})
    monkeypatch.setattr(
        "hermes_cli.codex_models.get_codex_model_ids", lambda access_token=None: ["gpt-5.4"]
    )

    assert connect_bit_provider("openai-codex") == "openai-codex"
    assert added == []


def test_cli_callback_installation_tolerates_removed_skills_tool(monkeypatch):
    """The coding-only wheel must start without the excluded skills module."""
    import builtins

    pytest.importorskip("prompt_toolkit")
    import cli

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "tools.skills_tool":
            raise ModuleNotFoundError("No module named 'tools.skills_tool'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    assert cli.set_secret_capture_callback(lambda *_args: None) is None


def test_conversation_loop_does_not_import_removed_skill_provenance():
    """A clean wheel must reach the real chat loop without skill modules."""
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import agent.conversation_loop; "
                "from tools.write_origin import ("
                "get_current_write_origin, set_current_write_origin); "
                "set_current_write_origin('assistant_tool'); "
                "assert get_current_write_origin() == 'assistant_tool'; "
                "print('ok')"
            ),
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_removed_skill_runtime_modules_have_no_production_imports():
    """Prevent another clean-install crash from a stale removed-module import."""
    project_root = Path(__file__).resolve().parents[1]
    forbidden = (
        "tools.skill_provenance",
        "tools.managed_tool_gateway",
        "tools.tool_search",
    )
    production_roots = (
        project_root / "agent",
        project_root / "tools",
        project_root / "hermes_cli",
        project_root / "cli.py",
        project_root / "run_agent.py",
    )
    offenders = []
    for root in production_roots:
        paths = [root] if root.is_file() else root.rglob("*.py")
        for path in paths:
            source = path.read_text(encoding="utf-8")
            for module in forbidden:
                if f"from {module} import" in source or f"import {module}" in source:
                    offenders.append(f"{path.relative_to(project_root)}: {module}")

    assert offenders == []


def test_bit_status_does_not_probe_or_launch_antigravity(monkeypatch):
    import hermes_cli.auth as auth
    import hermes_cli.antigravity as antigravity
    from hermes_cli.bithumb_onboarding import show_bit_status

    output = []
    monkeypatch.setattr(auth, "get_codex_auth_status", lambda: {"logged_in": True})
    monkeypatch.setattr(antigravity, "resolve_antigravity_executable", lambda: "/usr/bin/agy")
    monkeypatch.setattr(
        antigravity,
        "probe_antigravity_login",
        lambda *_args, **_kwargs: pytest.fail("status must not launch Antigravity"),
    )

    show_bit_status(emit=output.append)

    assert any("GPT" in line and "로그인됨" in line for line in output)
    assert any("Gemini" in line and "CLI 설치됨" in line for line in output)


def test_startup_tips_do_not_advertise_removed_or_api_key_features():
    from hermes_cli.tips import BITHUMB_AGENT_TIPS

    joined = "\n".join(BITHUMB_AGENT_TIPS).lower()
    for forbidden in (
        "hermes",
        "api key",
        "gateway",
        "mcp",
        "plugin",
        "skill install",
        "browser tool",
        "cron",
        "yolo",
    ):
        assert forbidden not in joined


def test_agent_import_has_no_removed_delegation_restore_warning():
    result = subprocess.run(
        [sys.executable, "-c", "import run_agent; print('ok')"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "ok"
    assert "async delegation" not in result.stderr.lower()


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
