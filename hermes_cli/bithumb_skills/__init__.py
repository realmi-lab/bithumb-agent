# SPDX-License-Identifier: MIT
# Derived from Hermes Agent (Copyright (c) 2025 Nous Research) and customized
# for the independent Bithumb Agent distribution. See LICENSE and NOTICE.md.

"""Immutable, package-local coding skills for Bithumb Agent.

The catalog is deliberately fixed. Skill names are resolved through an exact
allow-list and content is loaded only from resources shipped inside this
Python package. There is no user-directory scan, external path lookup,
installation, mutation, or runtime extension point here.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from types import MappingProxyType
from typing import Optional


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    """Public metadata for one bundled, read-only coding skill."""

    name: str
    description: str
    filename: str
    category: str = "coding"


_SKILLS = (
    SkillMetadata(
        name="systematic-debugging",
        description="재현과 증거를 바탕으로 원인을 좁히고 최소 수정으로 검증합니다.",
        filename="systematic-debugging.md",
    ),
    SkillMetadata(
        name="test-driven-development",
        description="실패 테스트, 최소 구현, 리팩터링 순서로 동작을 안전하게 만듭니다.",
        filename="test-driven-development.md",
    ),
    SkillMetadata(
        name="plan",
        description="코드를 먼저 조사한 뒤 파일 단위 실행 계획과 검증 기준을 작성합니다.",
        filename="plan.md",
    ),
    SkillMetadata(
        name="simplify-code",
        description="동작을 보존하면서 중복과 불필요한 복잡도를 줄입니다.",
        filename="simplify-code.md",
    ),
    SkillMetadata(
        name="requesting-code-review",
        description="변경 범위를 근거로 정확성, 보안, 호환성 위험을 점검합니다.",
        filename="requesting-code-review.md",
    ),
    SkillMetadata(
        name="spike",
        description="한 가지 기술적 불확실성을 작은 실험으로 빠르게 검증합니다.",
        filename="spike.md",
    ),
)

_SKILLS_BY_NAME = MappingProxyType({skill.name: skill for skill in _SKILLS})


def list_skill_metadata() -> tuple[SkillMetadata, ...]:
    """Return the complete immutable catalog in display order."""

    return _SKILLS


def get_skill_metadata(name: str) -> Optional[SkillMetadata]:
    """Resolve a skill by exact catalog name; paths and aliases are invalid."""

    if not isinstance(name, str):
        return None
    return _SKILLS_BY_NAME.get(name.strip())


def read_skill(name: str) -> Optional[str]:
    """Read one exact, bundled resource or return None for an unknown name."""

    skill = get_skill_metadata(name)
    if skill is None:
        return None
    return files(__package__).joinpath(skill.filename).read_text(encoding="utf-8")


__all__ = [
    "SkillMetadata",
    "get_skill_metadata",
    "list_skill_metadata",
    "read_skill",
]
