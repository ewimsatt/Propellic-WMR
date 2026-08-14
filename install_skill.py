#!/usr/bin/env python3
"""Install the lightweight text skill for Cursor, Codex, or both."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

SKILL_NAME = "clean-user-facing-text"
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "skills" / SKILL_NAME


@dataclass(frozen=True)
class Target:
    product: str
    skills_dir: Path

    @property
    def destination(self) -> Path:
        return self.skills_dir / SKILL_NAME


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _stage(target: Target) -> tuple[Path, Path]:
    target.skills_dir.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=f".{SKILL_NAME}.staging.", dir=target.skills_dir)
    )
    staged_skill = staging_root / SKILL_NAME
    try:
        shutil.copytree(SOURCE, staged_skill)
        if not (staged_skill / "SKILL.md").is_file():
            raise RuntimeError("staged skill is missing SKILL.md")
    except BaseException:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    return staging_root, staged_skill


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _activate(
    target: Target,
    staging_root: Path,
    staged_skill: Path,
    force: bool,
) -> Path | None:
    destination = target.destination
    backup: Path | None = None
    if _present(destination):
        if not force:
            raise FileExistsError(destination)
        backup = destination.with_name(
            f"{destination.name}.backup.{uuid.uuid4().hex[:12]}"
        )
        os.replace(destination, backup)

    try:
        os.replace(staged_skill, destination)
    except BaseException:
        if backup is not None and not _present(destination):
            os.replace(backup, destination)
        raise
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return backup


def _rollback(target: Target, backup: Path | None) -> None:
    _remove_path(target.destination)
    if backup is not None:
        os.replace(backup, target.destination)


def _targets(args: argparse.Namespace) -> list[Target]:
    selected: list[Target] = []
    if args.target in ("cursor", "all"):
        cursor_home = Path(
            args.cursor_home
            or os.environ.get("CURSOR_HOME", Path.home() / ".cursor")
        ).expanduser()
        selected.append(Target("Cursor", cursor_home / "skills"))
    if args.target in ("codex", "all"):
        codex_skills = Path(
            args.codex_skills_dir
            or os.environ.get("CODEX_SKILLS_DIR", Path.home() / ".agents" / "skills")
        ).expanduser()
        selected.append(Target("Codex", codex_skills))
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=("cursor", "codex", "all"), nargs="?", default="all")
    parser.add_argument("--force", action="store_true", help="Back up and replace existing installs")
    parser.add_argument("--cursor-home", help="Override Cursor home (default: ~/.cursor)")
    parser.add_argument(
        "--codex-skills-dir",
        help="Override Codex skill directory (default: ~/.agents/skills)",
    )
    args = parser.parse_args()

    targets = _targets(args)
    conflicts = [target.destination for target in targets if _present(target.destination)]
    if conflicts and not args.force:
        for conflict in conflicts:
            print(f"already exists: {conflict}", file=sys.stderr)
        print("No changes made. Re-run with --force to back up and replace.", file=sys.stderr)
        return 1

    staged: list[tuple[Target, Path, Path]] = []
    try:
        for target in targets:
            staged.append((target, *_stage(target)))
    except BaseException:
        for _target, staging_root, _staged_skill in staged:
            shutil.rmtree(staging_root, ignore_errors=True)
        raise

    activated: list[tuple[Target, Path | None]] = []
    try:
        for target, staging_root, staged_skill in staged:
            backup = _activate(target, staging_root, staged_skill, args.force)
            activated.append((target, backup))
    except BaseException:
        for target, backup in reversed(activated):
            _rollback(target, backup)
        for _target, staging_root, _staged_skill in staged:
            shutil.rmtree(staging_root, ignore_errors=True)
        raise

    for target, backup in activated:
        if backup is not None:
            print(f"{target.product}: backed up existing skill to {backup}")
        print(f"{target.product}: installed {target.destination}")

    print("Start a new session if the skill does not appear automatically.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
