import asyncio

import pytest
from fastapi import HTTPException

from hermes_cli import auth, models
from hermes_cli.web_server import (
    CredentialPoolAdd,
    EnvVarUpdate,
    _build_oauth_catalog,
    _is_bithumb_agent_inference_credential_key,
    add_credential_pool_entry,
    get_model_options,
    list_oauth_providers,
    set_env_var,
)


def test_dashboard_oauth_catalog_is_closed_to_two_providers(monkeypatch):
    monkeypatch.setattr(
        "hermes_cli.web_server._resolve_provider_status",
        lambda provider_id, status_fn: {"logged_in": provider_id == "openai-codex"},
    )

    catalog = _build_oauth_catalog()
    response = asyncio.run(list_oauth_providers())

    assert [row["id"] for row in catalog] == [
        "openai-codex",
        "antigravity-cli",
    ]
    assert [row["id"] for row in response["providers"]] == [
        "openai-codex",
        "antigravity-cli",
    ]
    assert all("bithumb-agent auth add" in row["cli_command"] for row in catalog)


def test_dashboard_model_options_never_include_api_key_or_custom_providers(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_auth_status",
        lambda provider_id=None: {"logged_in": True, "provider": provider_id},
    )
    monkeypatch.setattr(
        models,
        "cached_provider_model_ids",
        lambda provider_id: {
            "openai-codex": ["gpt-test"],
            "antigravity-cli": ["auto"],
        }[provider_id],
    )

    payload = get_model_options(include_unconfigured=True)

    assert [row["slug"] for row in payload["providers"]] == [
        "openai-codex",
        "antigravity-cli",
    ]
    assert all(row["source"] != "user-config" for row in payload["providers"])


def test_dashboard_rejects_inference_api_keys_and_manual_key_pools():
    assert _is_bithumb_agent_inference_credential_key("OPENROUTER_API_KEY") is True
    assert _is_bithumb_agent_inference_credential_key("GEMINI_API_KEY") is True
    assert _is_bithumb_agent_inference_credential_key("GITHUB_TOKEN") is False

    with pytest.raises(HTTPException, match="OAuth-only"):
        asyncio.run(
            set_env_var(
                EnvVarUpdate(key="OPENROUTER_API_KEY", value="not-saved"),
            )
        )

    with pytest.raises(HTTPException, match="OAuth-only"):
        asyncio.run(
            add_credential_pool_entry(
                CredentialPoolAdd(provider="openrouter", api_key="not-saved"),
            )
        )
