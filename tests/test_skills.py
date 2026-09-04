"""Tests for bundled Agent Skill validity and transactional installation."""

from __future__ import annotations

import os
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
import yaml

from cobruh import ConfigError
from cobruh.skills import install_skills, list_skills

EXPECTED_SKILLS = ["cobruh-config", "cobruh-mcp", "cobruh-runtime"]
PROJECT_DESTINATIONS = {
    "codex": ".agents/skills",
    "claude": ".claude/skills",
    "copilot": ".github/skills",
    "cursor": ".cursor/skills",
}
USER_DESTINATIONS = {
    "codex": ".agents/skills",
    "claude": ".claude/skills",
    "copilot": ".copilot/skills",
    "cursor": ".cursor/skills",
}


def test_bundled_skills_follow_agent_skills_metadata_rules() -> None:
    assert list_skills() == EXPECTED_SKILLS
    root = files("cobruh").joinpath("_skills")
    for name in EXPECTED_SKILLS:
        skill = root.joinpath(name, "SKILL.md")
        text = skill.read_text(encoding="utf-8")
        assert len(text.splitlines()) < 500
        assert text.startswith("---\n")
        _, frontmatter, body = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        assert metadata["name"] == name
        assert isinstance(metadata["description"], str) and len(metadata["description"]) > 40
        assert metadata["license"] == "MIT"
        assert body.strip()


@pytest.mark.parametrize("agent,destination", PROJECT_DESTINATIONS.items())
def test_project_install_destinations(tmp_path: Path, agent: str, destination: str) -> None:
    installed = install_skills(agent=agent, scope="project", project=tmp_path)
    expected = [str(tmp_path / destination / name) for name in EXPECTED_SKILLS]
    assert installed == expected
    assert all((Path(path) / "SKILL.md").is_file() for path in installed)
    assert install_skills(agent=agent, scope="project", project=tmp_path) == expected


@pytest.mark.parametrize("agent,destination", USER_DESTINATIONS.items())
def test_user_install_destinations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    agent: str,
    destination: str,
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    installed = install_skills(
        agent=agent,
        scope="user",
        project=Path("~/must-not-be-used"),
        names=["cobruh-config"],
    )
    assert installed == [str(home / destination / "cobruh-config")]
    assert (Path(installed[0]) / "SKILL.md").is_file()


def test_conflict_preflight_is_all_or_nothing_and_force_is_scoped(tmp_path: Path) -> None:
    conflict = tmp_path / ".cursor/skills/cobruh-config"
    conflict.mkdir(parents=True)
    (conflict / "SKILL.md").write_text("different", encoding="utf-8")

    with pytest.raises(ConfigError, match="differs"):
        install_skills(
            agent="all",
            scope="project",
            project=tmp_path,
            names=["cobruh-config"],
        )
    assert not (tmp_path / ".agents/skills/cobruh-config").exists()
    assert (conflict / "SKILL.md").read_text(encoding="utf-8") == "different"

    install_skills(
        agent="cursor",
        scope="project",
        project=tmp_path,
        names=["cobruh-config"],
        force=True,
    )
    assert (
        (conflict / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname: cobruh-config")
    )


def test_mutation_failure_rolls_back_prior_agents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import cobruh.skills as skills_module

    original_replace = os.replace
    failed = False

    def fail_once(source: Any, destination: Any) -> None:
        nonlocal failed
        if not failed and str(destination).endswith(".claude/skills/cobruh-config"):
            failed = True
            raise OSError("injected rename failure")
        original_replace(source, destination)

    monkeypatch.setattr(skills_module.os, "replace", fail_once)
    with pytest.raises(OSError, match="injected rename failure"):
        install_skills(
            agent="all",
            scope="project",
            project=tmp_path,
            names=["cobruh-config"],
        )
    assert not (tmp_path / ".agents/skills/cobruh-config").exists()
    assert not (tmp_path / ".claude/skills/cobruh-config").exists()


def test_unknown_skill_and_destination_symlink_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Unknown bundled skill"):
        install_skills(agent="codex", project=tmp_path, names=["missing"])

    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / ".agents"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(ConfigError, match="symlink"):
        install_skills(agent="codex", project=tmp_path)
