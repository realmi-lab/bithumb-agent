"""Security and packaging checks for the fixed Bithumb coding-skill catalog."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import tomllib
from types import SimpleNamespace


EXPECTED_SKILLS = {
    "systematic-debugging",
    "test-driven-development",
    "plan",
    "simplify-code",
    "requesting-code-review",
    "spike",
}


def test_catalog_is_exactly_six_immutable_package_resources():
    from hermes_cli.bithumb_skills import list_skill_metadata, read_skill

    metadata = list_skill_metadata()
    assert isinstance(metadata, tuple)
    assert {item.name for item in metadata} == EXPECTED_SKILLS
    assert len(metadata) == len(EXPECTED_SKILLS)
    assert {item.category for item in metadata} == {"coding"}

    for item in metadata:
        content = read_skill(item.name)
        assert content is not None
        assert f"name: {item.name}" in content
        assert "license: MIT" in content
        assert "attribution:" in content
        assert "read_only: true" in content


def test_exact_name_resolution_rejects_paths_and_unknown_names():
    from hermes_cli.bithumb_skills import get_skill_metadata, read_skill
    from tools.bithumb_skills_tool import skill_view

    for value in (
        "../systematic-debugging",
        "../../etc/passwd",
        "/tmp/systematic-debugging",
        "systematic-debugging.md",
        "SYSTEMATIC-DEBUGGING",
        "unknown",
    ):
        assert get_skill_metadata(value) is None
        assert read_skill(value) is None
        result = json.loads(skill_view(value))
        assert result["success"] is False
        assert "content" not in result


def test_read_only_tools_list_and_view_only_bundled_content():
    from tools.bithumb_skills_tool import skill_view, skills_list

    listing = json.loads(skills_list())
    assert listing["success"] is True
    assert listing["count"] == 6
    assert listing["read_only"] is True
    assert {item["name"] for item in listing["skills"]} == EXPECTED_SKILLS
    assert all(item["read_only"] is True for item in listing["skills"])

    viewed = json.loads(skill_view("systematic-debugging"))
    assert viewed["success"] is True
    assert viewed["source"] == "bithumb-agent-bundled"
    assert viewed["read_only"] is True
    assert "# Systematic Debugging" in viewed["content"]


def test_skill_tool_has_no_dynamic_or_executable_dependencies():
    project_root = Path(__file__).resolve().parents[1]
    module_path = project_root / "tools" / "bithumb_skills_tool.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    assert imported <= {
        "__future__",
        "json",
        "hermes_cli.bithumb_skills",
        "tools.registry",
    }

    source = module_path.read_text(encoding="utf-8")
    for forbidden in (
        "subprocess",
        "tools.skills_tool",
        "skills_hub",
        "skill_provenance",
        "managed_tool_gateway",
        "credential_file",
        "env_passthrough",
        "delegate_task",
    ):
        assert forbidden not in source


def test_skill_documents_do_not_embed_install_network_or_delegation_actions():
    from hermes_cli.bithumb_skills import list_skill_metadata, read_skill

    forbidden = (
        "delegate_task",
        "skill_manage",
        "pip install",
        "npm install",
        "curl ",
        "wget ",
        "http://",
        "https://",
        "subprocess",
    )
    for item in list_skill_metadata():
        content = (read_skill(item.name) or "").lower()
        for token in forbidden:
            assert token not in content, f"{item.name} contains {token!r}"


def test_model_runtime_exposes_read_only_skill_tools_but_not_management():
    import model_tools

    exposed = {
        entry["function"]["name"]
        for entry in model_tools.get_tool_definitions(quiet_mode=True)
    }
    assert {"skills_list", "skill_view"} <= exposed
    assert "skill_manage" not in exposed

    viewed = json.loads(
        model_tools.handle_function_call("skill_view", {"name": "plan"})
    )
    assert viewed["success"] is True
    blocked = json.loads(
        model_tools.handle_function_call(
            "skill_view", {"name": "../../outside"}
        )
    )
    assert blocked["success"] is False


def test_model_tool_import_has_no_missing_optional_module_warning():
    project_root = Path(__file__).resolve().parents[1]
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import model_tools; "
                "model_tools.get_tool_definitions(quiet_mode=True); "
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
    assert "No module named" not in result.stderr
    assert "Tool search assembly skipped" not in result.stderr


def test_system_prompt_advertises_only_the_fixed_read_only_catalog():
    from tools.bithumb_skills_tool import build_bithumb_skills_system_prompt

    prompt = build_bithumb_skills_system_prompt()
    for name in EXPECTED_SKILLS:
        assert name in prompt
    assert "immutable and read-only" in prompt
    assert "skill_manage" not in prompt
    assert "~/.hermes" not in prompt
    assert "plugin" not in prompt.lower()


def test_real_system_prompt_uses_bithumb_identity_and_no_dynamic_skill_hints():
    from agent.system_prompt import build_system_prompt_parts

    agent = SimpleNamespace(
        context_compressor=None,
        # Include an invalid upstream management name to prove prompt
        # assembly still fails closed to the static Bithumb catalog.
        valid_tool_names={"skills_list", "skill_view", "skill_manage"},
        _task_completion_guidance=False,
        _parallel_tool_call_guidance=False,
        _tool_use_enforcement=False,
        model="gpt-5.4",
        provider="openai-codex",
        platform="cli",
        _environment_probe=False,
        skip_context_files=True,
        _memory_store=None,
        _memory_enabled=False,
        _user_profile_enabled=False,
        _memory_manager=None,
        pass_session_id=False,
        session_id=None,
        _platform_hint_overrides={},
    )

    stable = build_system_prompt_parts(agent)["stable"]
    assert "You are Bithumb Agent" in stable
    assert "You are Hermes Agent" not in stable
    assert "hermes-agent.nousresearch.com" not in stable
    assert "systematic-debugging" in stable
    assert "skill_manage" not in stable
    assert "~/.hermes" not in stable
    assert "cronjob" not in stable


def test_interactive_skills_command_is_read_only():
    from tools.bithumb_skills_tool import format_skills_cli

    listing = format_skills_cli("/skills")
    assert "READ-ONLY CODING SKILLS" in listing
    assert EXPECTED_SKILLS <= set(listing.replace("—", " ").split())

    viewed = format_skills_cli("/skills view spike")
    assert "# Technical Spike" in viewed

    for command in (
        "/skills install anything",
        "/skills edit plan",
        "/skills search remote",
        "/skills approve pending",
    ):
        result = format_skills_cli(command)
        assert "읽기 전용" in result
        assert "제공하지 않습니다" in result


def test_packaging_declares_markdown_resources_and_excludes_upstream_catalog():
    project_root = Path(__file__).resolve().parents[1]
    with (project_root / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    package_data = pyproject["tool"]["setuptools"]["package-data"]
    assert package_data["hermes_cli.bithumb_skills"] == ["*.md"]

    manifest = (project_root / "MANIFEST.in").read_text(encoding="utf-8")
    assert "graft hermes_cli/bithumb_skills" in manifest
    assert "prune skills" in manifest


def test_cli_does_not_scan_or_reload_external_skill_directories():
    project_root = Path(__file__).resolve().parents[1]
    cli_source = (project_root / "cli.py").read_text(encoding="utf-8")
    banner_source = (project_root / "hermes_cli" / "banner.py").read_text(
        encoding="utf-8"
    )

    ensure_start = cli_source.index("def _ensure_skill_commands()")
    ensure_end = cli_source.index("\ndef get_skill_commands()", ensure_start)
    ensure_source = cli_source[ensure_start:ensure_end]
    assert "scan_skill_commands" not in ensure_source

    reload_start = cli_source.index("    def _reload_skills(self)")
    reload_end = cli_source.index("\n    # ====", reload_start)
    reload_source = cli_source[reload_start:reload_end]
    assert "agent.skill_commands" not in reload_source
    assert "result = reload_skills" not in reload_source

    assert "tools.skills_tool" not in banner_source
    assert "_find_all_skills" not in banner_source
