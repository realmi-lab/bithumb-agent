"""Bithumb Agent's two-provider OAuth onboarding commands."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Callable


ORANGE = "\033[38;2;255;92;0m"
WHITE = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_bit_help(*, emit: Callable[[str], None] = print) -> None:
    """Print the exact first-login commands supported by Bithumb Agent."""
    emit("")
    emit(f"{BOLD}{ORANGE}BITHUMB AGENT · OAuth Login{RESET}")
    emit(f"{WHITE}  /bit gpt     ChatGPT/Codex 로그인 창 열기{RESET}")
    emit(f"{WHITE}  /bit gemini  Google Antigravity 로그인 열기{RESET}")
    emit(f"{DIM}  /bit status  로그인 상태 확인 · /exit 종료{RESET}")
    emit("")


def print_first_run_screen(*, emit: Callable[[str], None] = print) -> None:
    """Render the small, dependency-free screen shown before OAuth exists."""
    emit("")
    emit(f"{BOLD}{ORANGE}╭────────────────────────────────────────────────────────╮{RESET}")
    emit(f"{BOLD}{ORANGE}│                    BITHUMB AGENT                       │{RESET}")
    emit(f"{BOLD}{ORANGE}╰────────────────────────────────────────────────────────╯{RESET}")
    emit(f"{BOLD}{ORANGE}OPEN-SOURCE CUSTOMIZATION{RESET}")
    emit(f"{WHITE}오픈소스를 빗썸에 맞게 바꾼 것입니다.{RESET}")
    emit(f"{WHITE}ilhong.kim@bithumbcorp.com{RESET}")
    print_bit_help(emit=emit)


def _normalize_bit_target(command: str) -> str | None:
    parts = (command or "").strip().lower().split()
    if not parts or parts[0] not in {"/bit", "bit"}:
        return None
    if len(parts) == 1 or parts[1] in {"help", "도움말"}:
        return "help"
    aliases = {
        "gpt": "openai-codex",
        "chatgpt": "openai-codex",
        "codex": "openai-codex",
        "gemini": "antigravity-cli",
        "google": "antigravity-cli",
        "antigravity": "antigravity-cli",
        "agy": "antigravity-cli",
        "status": "status",
    }
    return aliases.get(parts[1])


def connect_bit_provider(provider: str) -> str:
    """Run the reviewed OAuth flow and select the connected provider."""
    from hermes_cli.auth_commands import auth_add_command

    auth_add_command(
        SimpleNamespace(provider=provider, auth_type="oauth", label=None)
    )

    # ``auth add`` preserves an existing selection for multi-account users.
    # A direct `/bit` request is an explicit selection, so make it active.
    from hermes_cli import auth as auth_mod

    if provider == "openai-codex":
        base_url = auth_mod.DEFAULT_CODEX_BASE_URL
        # Codex requires a concrete model name. Prefer the first model visible
        # to this account, with a stable built-in fallback when discovery is
        # temporarily unavailable.
        default_model = "gpt-5.4"
        try:
            from hermes_cli.codex_models import get_codex_model_ids

            status = auth_mod.get_codex_auth_status()
            models = get_codex_model_ids(access_token=status.get("api_key"))
            if models:
                default_model = models[0]
        except Exception:
            pass
    else:
        base_url = auth_mod.DEFAULT_ANTIGRAVITY_CLI_BASE_URL
        # The official Antigravity CLI owns its model choice.
        default_model = "auto"
    auth_mod._update_config_for_provider(provider, base_url, default_model)
    return provider


def show_bit_status(*, emit: Callable[[str], None] = print) -> None:
    from hermes_cli.auth import get_auth_status

    labels = (
        ("GPT", "openai-codex"),
        ("Gemini", "antigravity-cli"),
    )
    for label, provider in labels:
        try:
            ready = bool(get_auth_status(provider).get("logged_in"))
        except Exception:
            ready = False
        state = "로그인됨" if ready else "로그아웃"
        emit(f"  {label:<7} {state}")


def handle_bit_command(
    command: str,
    *,
    emit: Callable[[str], None] = print,
    connector: Callable[[str], str] = connect_bit_provider,
) -> str | None:
    """Handle one ``/bit`` command and return the selected provider, if any."""
    target = _normalize_bit_target(command)
    if target == "help":
        print_bit_help(emit=emit)
        return None
    if target == "status":
        show_bit_status(emit=emit)
        return None
    if target not in {"openai-codex", "antigravity-cli"}:
        emit("사용법: /bit gpt 또는 /bit gemini")
        return None

    label = "ChatGPT/Codex" if target == "openai-codex" else "Google Antigravity"
    emit(f"{ORANGE}{label} OAuth 로그인을 시작합니다…{RESET}")
    selected = connector(target)
    emit(f"{ORANGE}✓ {label} 로그인이 연결되었습니다.{RESET}")
    return selected


def run_first_login_shell(
    *,
    input_fn: Callable[[str], str] = input,
    emit: Callable[[str], None] = print,
    connector: Callable[[str], str] = connect_bit_provider,
) -> str | None:
    """Wait for ``/bit gpt`` or ``/bit gemini`` before the agent is built."""
    print_first_run_screen(emit=emit)
    while True:
        try:
            command = input_fn(f"{BOLD}{ORANGE}bithumb-agent>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            emit("")
            return None

        if not command:
            continue
        if command.lower() in {"/exit", "/quit", "exit", "quit"}:
            return None
        try:
            selected = handle_bit_command(
                command,
                emit=emit,
                connector=connector,
            )
        except SystemExit as exc:
            if exc.code not in {None, 0}:
                emit(str(exc.code))
            continue
        except Exception as exc:
            emit(f"로그인에 실패했습니다: {exc}")
            continue
        if selected:
            return selected
