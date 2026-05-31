#!/usr/bin/env python3
"""Install one or all skills from this repository into Codex and/or Hermes."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODEX_DIR = Path.home() / ".codex" / "skills"
DEFAULT_HERMES_DIR = (
    Path.home()
    / ".hermes"
    / "hermes-agent"
    / "optional-skills"
    / "software-development"
)


def copy_skill(skill_name: str, destination_root: Path) -> Path:
    source = REPO_ROOT / "skills" / skill_name
    if not source.exists():
        raise SystemExit(f"Skill not found: {source}")
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"Invalid skill, missing SKILL.md: {source}")

    destination = destination_root / skill_name
    destination_root.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return destination


def available_skills() -> list[str]:
    skills_dir = REPO_ROOT / "skills"
    if not skills_dir.exists():
        return []
    return sorted(
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", help="skill name under skills/, or 'all'")
    parser.add_argument(
        "--target",
        choices=("codex", "hermes", "all"),
        default="codex",
        help="install target",
    )
    parser.add_argument("--codex-dir", type=Path, default=DEFAULT_CODEX_DIR)
    parser.add_argument("--hermes-dir", type=Path, default=DEFAULT_HERMES_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_names = available_skills() if args.skill == "all" else [args.skill]
    if not skill_names:
        raise SystemExit("No skills found under skills/")

    installed = []
    for skill_name in skill_names:
        if args.target in {"codex", "all"}:
            installed.append((skill_name, copy_skill(skill_name, args.codex_dir)))
        if args.target in {"hermes", "all"}:
            installed.append((skill_name, copy_skill(skill_name, args.hermes_dir)))

    for skill_name, path in installed:
        print(f"Installed {skill_name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
