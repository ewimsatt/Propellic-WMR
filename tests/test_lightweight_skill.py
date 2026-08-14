"""Smoke tests for the standalone Cursor/Codex text skill."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import install_skill

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "clean-user-facing-text"


def test_lightweight_clean_text_cli():
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "clean_text.py"), "-", "--stats"],
        input="Hello\u200b world\u3000again",
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.rstrip("\n") == "Hello world again"
    assert '"removed_count": 1' in result.stderr
    assert '"replaced_count": 1' in result.stderr


def test_lightweight_skill_has_no_template_placeholders():
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert "TODO" not in skill_text
    assert (SKILL / "agents" / "openai.yaml").is_file()
    assert (SKILL / "references" / "watermark-notes.md").is_file()


def _run_installer(home: Path, *args: str, check: bool = True):
    env = os.environ.copy()
    env.pop("CURSOR_HOME", None)
    env.pop("CODEX_SKILLS_DIR", None)
    env.update({"HOME": str(home), "USERPROFILE": str(home)})
    return subprocess.run(
        [sys.executable, str(ROOT / "install_skill.py"), *args],
        env=env,
        text=True,
        capture_output=True,
        check=check,
    )


def test_installer_all_uses_current_cursor_and_codex_locations(tmp_path):
    _run_installer(tmp_path, "all")

    assert (tmp_path / ".cursor" / "skills" / SKILL.name / "SKILL.md").is_file()
    assert (tmp_path / ".agents" / "skills" / SKILL.name / "SKILL.md").is_file()


def test_installer_preflights_all_targets_before_changing_any(tmp_path):
    cursor_install = tmp_path / ".cursor" / "skills" / SKILL.name
    cursor_install.mkdir(parents=True)
    (cursor_install / "sentinel").write_text("keep", encoding="utf-8")

    result = _run_installer(tmp_path, "all", check=False)

    assert result.returncode == 1
    assert (cursor_install / "sentinel").read_text(encoding="utf-8") == "keep"
    assert not (tmp_path / ".agents" / "skills" / SKILL.name).exists()


def test_installer_force_creates_backup_and_replaces(tmp_path):
    destination = tmp_path / ".agents" / "skills" / SKILL.name
    destination.mkdir(parents=True)
    (destination / "old").write_text("old", encoding="utf-8")

    _run_installer(tmp_path, "codex", "--force")

    backups = list(destination.parent.glob(f"{SKILL.name}.backup.*"))
    assert len(backups) == 1
    assert (backups[0] / "old").read_text(encoding="utf-8") == "old"
    assert (destination / "SKILL.md").is_file()


def test_installer_all_rolls_back_first_target_if_second_activation_fails(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("CURSOR_HOME", raising=False)
    monkeypatch.delenv("CODEX_SKILLS_DIR", raising=False)
    monkeypatch.setattr(sys, "argv", ["install_skill.py", "all"])

    real_activate = install_skill._activate
    calls = 0

    def fail_second_activation(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated activation failure")
        return real_activate(*args, **kwargs)

    monkeypatch.setattr(install_skill, "_activate", fail_second_activation)

    with pytest.raises(OSError, match="simulated activation failure"):
        install_skill.main()

    assert not (tmp_path / ".cursor" / "skills" / SKILL.name).exists()
    assert not (tmp_path / ".agents" / "skills" / SKILL.name).exists()
    assert not list(tmp_path.rglob("*.staging.*"))
