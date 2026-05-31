#!/usr/bin/env python3
"""Deterministic project hygiene audit for agent-managed repositories."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


NOISY_DIRS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
}
RUNTIME_DIRS = {"data", "logs"}
TEMP_ROOT_PATTERNS = ("_tmp", "_test", "tmp_", "test2", "scratch", "fix")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def has_git(root: Path) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def git_ignored(root: Path, path: str) -> bool:
    if not has_git(root):
        return False
    return subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def scan(root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []

    if not (root / "AGENTS.md").exists():
        findings.append(("WARN", "missing AGENTS.md for standing agent rules"))

    docs = root / "docs"
    if docs.exists() and not (docs / "DOCS_INDEX.md").exists():
        findings.append(("WARN", "docs/ exists but docs/DOCS_INDEX.md is missing"))

    if has_git(root):
        for item in [".env", "data", "logs", "venv", ".venv", "__pycache__"]:
            if (root / item).exists() and not git_ignored(root, item):
                findings.append(("BLOCK", f"{item} exists but is not ignored by git"))
    else:
        findings.append(("WARN", "not a git repository; diffs and hygiene enforcement are weaker"))

    for path in root.iterdir():
        name = path.name
        if name in NOISY_DIRS:
            continue
        if path.is_file() and name.endswith((".py", ".sh", ".js", ".ts")):
            stem = path.stem.lower()
            if stem.startswith(TEMP_ROOT_PATTERNS):
                findings.append(("WARN", f"root-level temporary script: {name}"))

    for dirname in RUNTIME_DIRS:
        path = root / dirname
        if path.exists() and not git_ignored(root, dirname):
            findings.append(("BLOCK", f"runtime directory should be ignored: {dirname}/"))

    agents = root / "AGENTS.md"
    if agents.exists():
        text = agents.read_text(encoding="utf-8", errors="replace")
        bad_markers = ["## 当前配置", "## 目录结构", "根因回顾", "## 当前优先级", "后续 agent 应"]
        for marker in bad_markers:
            if marker in text:
                findings.append(("WARN", f"AGENTS.md appears to contain task/detail content: {marker}"))
        if len(text.splitlines()) > 180:
            findings.append(("WARN", "AGENTS.md is long; consider moving details to docs/"))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="project root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    findings = scan(root)
    print(f"Project hygiene audit: {root}")
    if not findings:
        print("PASS: no hygiene issues found")
        return 0

    exit_code = 0
    for level, message in findings:
        print(f"{level}: {message}")
        if level == "BLOCK":
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
