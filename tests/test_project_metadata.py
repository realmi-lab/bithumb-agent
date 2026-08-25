"""Regression tests for Bithumb Agent packaging metadata."""

from pathlib import Path
import tomllib


def _load_pyproject():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        return tomllib.load(handle)


def test_requirements_file_matches_core_project_dependencies():
    project_root = Path(__file__).resolve().parents[1]
    requirements = [
        line.strip()
        for line in (project_root / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    assert requirements == _load_pyproject()["project"]["dependencies"]


def test_only_development_extra_is_published():
    optional = _load_pyproject()["project"]["optional-dependencies"]

    assert set(optional) == {"dev"}
    assert all("bithumb-agent[" not in requirement for requirement in optional["dev"])


def test_distribution_excludes_disabled_integration_packages():
    setuptools = _load_pyproject()["tool"]["setuptools"]
    package_includes = setuptools["packages"]["find"]["include"]
    package_excludes = setuptools["packages"]["find"]["exclude"]
    py_modules = setuptools["py-modules"]

    for name in ("gateway", "cron", "plugins", "tui_gateway", "acp_adapter"):
        assert name not in package_includes
        assert f"{name}.*" not in package_includes
    assert "hermes_cli.dashboard_auth" in package_excludes
    assert "hermes_cli.proxy" in package_excludes
    assert "mcp_serve" not in py_modules


def test_mit_license_provenance_and_customization_record_are_published():
    project_root = Path(__file__).resolve().parents[1]
    project = _load_pyproject()["project"]

    assert project["license"] == "MIT"
    assert set(project["license-files"]) == {
        "LICENSE",
        "NOTICE.md",
        "CUSTOMIZATION.md",
    }

    license_text = (project_root / "LICENSE").read_text(encoding="utf-8")
    notice_text = (project_root / "NOTICE.md").read_text(encoding="utf-8")
    customization_text = (project_root / "CUSTOMIZATION.md").read_text(
        encoding="utf-8"
    )
    normalized_customization = " ".join(customization_text.split())

    assert license_text.startswith("MIT License\n")
    assert "Copyright (c) 2025 Nous Research" in license_text
    assert "permission notice shall be included" in license_text
    assert "https://github.com/NousResearch/hermes-agent" in notice_text
    assert "SPDX-License-Identifier: MIT" in notice_text
    assert "does not replace or modify, the MIT License" in notice_text
    assert "How Hermes Agent was changed into Bithumb Agent" in normalized_customization
    assert "Google Antigravity source code is not claimed" in normalized_customization
    assert "not an official Bithumb product" in normalized_customization


def test_bithumb_specific_modules_have_spdx_and_provenance_headers():
    project_root = Path(__file__).resolve().parents[1]
    for relative_path in (
        "hermes_cli/bithumb_agent_entry.py",
        "hermes_cli/bithumb_agent_policy.py",
        "hermes_cli/bithumb_onboarding.py",
    ):
        lines = (project_root / relative_path).read_text(encoding="utf-8").splitlines()
        assert lines[0] == "# SPDX-License-Identifier: MIT"
        assert "Derived from Hermes Agent" in lines[1]
