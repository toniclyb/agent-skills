# Agent Skills Repository Rules

This repository stores reusable agent skills. Keep it small, portable, and runtime-neutral.

## Layout

- `skills/<skill-name>/SKILL.md` is the required entrypoint.
- Skill-specific helpers stay inside that skill folder.
- Cross-skill repository utilities live in `scripts/`.
- Runtime-specific install targets must be configurable.

## Skill Rules

- Do not hardcode one project into a reusable skill.
- Put detailed standards in `references/`, not in `SKILL.md`, unless they are core workflow.
- Put deterministic checks in `scripts/`.
- Keep examples concise and portable.
- Validate each skill before committing.

## Release Rules

- No secrets, logs, caches, runtime state, or local generated reports.
- `git status --short` must be clean before publishing.
- Installation instructions in `README.md` must work from a fresh clone.

