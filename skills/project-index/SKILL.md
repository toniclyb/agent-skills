---
name: project-index
description: Use when a project needs a generated PROJECT_INDEX.md, two-tier AI-readable codebase index, module map, API detail index, or reusable index generation script. Trigger when the user mentions PROJECT_INDEX.md, 双层索引, project index, codebase index, moving/copying gen_index.py between repositories, or keeping agents oriented before code changes.
---

# Project Index

## Purpose

Generate and maintain a two-tier `PROJECT_INDEX.md` so agents can orient quickly without rereading an entire repository.

## What It Produces

- Tier 1: compact overview with modules, key symbols, dependencies, and reading guide.
- Tier 2: per-module API details with classes, functions, signatures, and dataclass fields.

By default the index avoids volatile git status, timestamps, and commit hashes. Use `--with-status` only for temporary local inspection.

## Quick Use

From any project root:

```bash
python ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md
```

Check only when stale:

```bash
python ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md --if-stale
```

Print to stdout:

```bash
python ~/.codex/skills/project-index/scripts/gen_index.py --root . --stdout
```

## Recommended Project Rule

Add this to the target project `AGENTS.md` when the project uses the index:

```markdown
Before code/config/doc changes, run:

python ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md --if-stale

After changes, run:

python ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md

Do not hand edit PROJECT_INDEX.md. Change the generator or project structure, then regenerate.
```

## When To Copy The Script

Prefer using the installed skill script directly. Copy `scripts/gen_index.py` into a project only when the project must work without installed skills, CI needs a repo-local generator, or the user explicitly asks for a vendored script.

## Validation

After installing or editing this skill:

```bash
python skills/project-index/scripts/gen_index.py --root . --stdout >/tmp/project-index-check.md
python -m py_compile skills/project-index/scripts/gen_index.py
```

