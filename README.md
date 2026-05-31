# Agent Skills

Reusable skills for Codex, Hermes, and other agent runtimes.

## Skills

| Skill | Purpose |
| --- | --- |
| `project-governance` | Project hygiene, documentation routing, script management, git hygiene, and agent development gates |

## Install

Install one skill into Codex:

```bash
python3 scripts/install_skill.py project-governance --target codex
```

Install one skill into Hermes optional skills:

```bash
python3 scripts/install_skill.py project-governance --target hermes
```

Install into both:

```bash
python3 scripts/install_skill.py project-governance --target all
```

Default paths:

- Codex: `~/.codex/skills/<skill-name>`
- Hermes: `~/.hermes/hermes-agent/optional-skills/software-development/<skill-name>`

Override paths:

```bash
python3 scripts/install_skill.py project-governance --codex-dir /path/to/skills --hermes-dir /path/to/optional-skills/software-development --target all
```

## Use From Another Machine

```bash
git clone <repo-url> agent-skills
cd agent-skills
python3 scripts/install_skill.py project-governance --target all
```

## Repository Rules

- Each skill lives under `skills/<skill-name>/`.
- Every skill must include `SKILL.md`.
- Optional resources stay inside the skill folder: `scripts/`, `references/`, `assets/`, `agents/`.
- Do not commit machine runtime state, logs, caches, credentials, or generated audit reports.
- Keep shared installation logic in `scripts/`.
