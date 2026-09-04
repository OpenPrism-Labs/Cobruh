"""Tests for the declared public API and built wheel contents."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import cobruh


def test_public_api_is_exact() -> None:
    assert cobruh.__version__ == "0.2.0"
    assert cobruh.__all__ == [
        "Cobruh",
        "CobruhError",
        "ConfigError",
        "OverrideError",
        "TargetError",
        "__version__",
    ]
    for name in cobruh.__all__:
        assert hasattr(cobruh, name)
    for removed in (
        "main",
        "initialize",
        "compose",
        "ConfigStore",
        "DictConfig",
        "ListConfig",
        "GlobalContext",
        "instantiate",
    ):
        assert not hasattr(cobruh, removed)


def test_wheel_contains_runtime_modules_typing_and_all_skills(tmp_path: Path) -> None:
    output = tmp_path / "dist"
    uv = shutil.which("uv")
    command = (
        [uv, "build", "--wheel", "--out-dir", str(output)]
        if uv is not None
        else [sys.executable, "-m", "build", "--wheel", "--outdir", str(output)]
    )
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    wheels = list(output.glob("cobruh-0.2.0-*.whl"))
    assert len(wheels) == 1

    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
        assert "cobruh/py.typed" in names
        assert "cobruh/project.py" in names
        assert "cobruh/composition.py" in names
        assert "cobruh/runtime.py" in names
        assert "cobruh/cli.py" in names
        assert "cobruh/mcp_server.py" in names
        assert "cobruh/skills.py" in names
        for skill in ("cobruh-config", "cobruh-mcp", "cobruh-runtime"):
            assert f"cobruh/_skills/{skill}/SKILL.md" in names
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")
        assert "Version: 0.2.0" in metadata
        assert "Requires-Python: <3.15,>=3.10" in metadata
        assert "Requires-Dist: PyYAML<7,>=6.0.3" in metadata
        assert 'Requires-Dist: mcp<3,>=2; extra == "agentic"' in metadata
