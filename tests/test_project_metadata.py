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
