# Agent Skills

Reusable skills for Codex, Hermes, and compatible agent runtimes.

This repository is meant to be cloned onto any machine and installed into the local agent skill directories. It contains portable agent operating procedures plus deterministic helper scripts.

## Available Skills

| Skill | Use when |
| --- | --- |
| `project-governance` | You need project hygiene, documentation routing, script management, git hygiene, `AGENTS.md` rules, review gates, or cleanup of scattered files. |
| `project-index` | You need a generated two-tier `PROJECT_INDEX.md` so agents can understand a repo before changing code. |

## Repository Layout

```text
agent-skills/
├── AGENTS.md
├── README.md
├── scripts/
│   └── install_skill.py
└── skills/
    ├── project-governance/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   ├── references/project-standards.md
    │   └── scripts/audit_project_hygiene.py
    └── project-index/
        ├── SKILL.md
        ├── agents/openai.yaml
        └── scripts/gen_index.py
```

## Install

Clone the repository:

```bash
git clone <repo-url> agent-skills
cd agent-skills
```

Install all skills into Codex:

```bash
python3 scripts/install_skill.py all --target codex
```

Install all skills into Hermes:

```bash
python3 scripts/install_skill.py all --target hermes
```

Install all skills into both:

```bash
python3 scripts/install_skill.py all --target all
```

Install one skill:

```bash
python3 scripts/install_skill.py project-governance --target all
python3 scripts/install_skill.py project-index --target all
```

Default install paths:

```text
Codex:  ~/.codex/skills/<skill-name>
Hermes: ~/.hermes/hermes-agent/optional-skills/software-development/<skill-name>
```

Override install paths:

```bash
python3 scripts/install_skill.py all \
  --target all \
  --codex-dir /path/to/codex/skills \
  --hermes-dir /path/to/hermes/optional-skills/software-development
```

## Use `project-governance`

Ask an agent to use `project-governance` when a repo feels messy or when it is about to change project structure, scripts, docs, or `AGENTS.md`.

Direct hygiene audit:

```bash
python3 ~/.codex/skills/project-governance/scripts/audit_project_hygiene.py /path/to/project
```

Typical uses:

- separate standing rules from task-state docs
- clean root-level temporary scripts
- design `docs/` routing
- check `.gitignore` and runtime file hygiene
- create or tighten `AGENTS.md`

## Use `project-index`

Generate an AI-readable two-tier index for a repo:

```bash
cd /path/to/project
python3 ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md
```

Regenerate only if stale:

```bash
python3 ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md --if-stale
```

Temporary local inspection with git status:

```bash
python3 ~/.codex/skills/project-index/scripts/gen_index.py --root . --stdout --with-status
```

Recommended `AGENTS.md` rule for projects using the index:

```markdown
Before code/config/doc changes:

python ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md --if-stale

After code/config/doc changes:

python ~/.codex/skills/project-index/scripts/gen_index.py --root . --output PROJECT_INDEX.md

Do not hand edit PROJECT_INDEX.md.
```

## Validate

Validate skill shape:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/project-governance
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/project-index
```

Validate helper scripts:

```bash
python3 skills/project-governance/scripts/audit_project_hygiene.py .
python3 skills/project-index/scripts/gen_index.py --root . --stdout >/tmp/project-index.md
python3 -m py_compile scripts/install_skill.py skills/project-index/scripts/gen_index.py skills/project-governance/scripts/audit_project_hygiene.py
```

## Maintenance Rules

- Each skill lives under `skills/<skill-name>/`.
- Every skill must include `SKILL.md`.
- Optional resources stay inside the skill folder: `scripts/`, `references/`, `assets/`, `agents/`.
- Do not commit secrets, logs, runtime state, caches, dependency folders, or generated audit reports.
- Keep installation and repository-level tooling in `scripts/`.
- Validate skills before publishing.
