# Project Governance Standards

## Document Classes

| Class | Purpose | Examples | Must not contain |
| --- | --- | --- | --- |
| Standing rules | Stable behavior constraints | `AGENTS.md` | dated plans, incident details, parameter snapshots |
| Architecture facts | Current system truth | `docs/architecture/current.md` | stale validation results, wishlists |
| Governance | Process and review gates | `docs/governance/*.md` | task queues, temporary priorities |
| Plans | Work to execute | `docs/plans/YYYY-MM-DD-topic.md` | permanent rules |
| Audit | Evidence and findings | `docs/audit/*.md` | hidden fixes, unverified claims |
| Research | Experiments and strategy work | `research/*.md`, `research/results/*` | production state truth |
| Runtime | Machine state | `data/`, `logs/` | source-controlled facts |

## Recommended Minimal Layout

```text
project/
├── AGENTS.md
├── PROJECT_INDEX.md              # optional, generated
├── .gitignore
├── docs/
│   ├── DOCS_INDEX.md
│   ├── architecture/
│   │   └── current.md
│   ├── governance/
│   ├── audit/
│   └── plans/
├── scripts/
│   └── tmp/                      # optional, ignored or routinely cleaned
├── tests/
├── data/                         # ignored
└── logs/                         # ignored
```

Use the layout as a routing standard, not a reason to create empty directories in tiny projects.

## AGENTS.md Standard

Keep `AGENTS.md` short enough that every agent can read it fully. Good sections:

- purpose
- required reading order
- architecture hard boundaries
- non-negotiable invariants
- development workflow gates
- documentation routing
- audit/review requirements

Move these out:

- current directory tree
- detailed module inventory
- dated audit reports
- task queues
- release notes
- incident narrative
- parameter tables
- generated command output

## Script Standard

Every script needs an owner class:

| Class | Location | Rule |
| --- | --- | --- |
| reusable automation | `scripts/` | named by action and domain |
| temporary exploration | `scripts/tmp/` | delete or ignore before handoff |
| operations wrapper | `scripts/` | dry-run where possible, documented inputs |
| generated helper | generator-owned location | never hand edit generated output |

Script names should be lowercase with underscores or hyphens. Avoid root-level `_tmp.py`, `test2.py`, `fix.py`, `new.py`, and similar names.

## Git Hygiene

`.gitignore` should cover:

- secrets: `.env`, credential files
- dependencies: `venv/`, `node_modules/`
- runtime: `data/`, `logs/`, pid files
- caches: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`
- generated reports when not meant for review
- temporary scripts and local scratch files

Do not commit runtime data unless it is a deliberate fixture under `tests/fixtures/`.

## Generated Files

Generated files must say how to regenerate them. Prefer:

```markdown
<!-- Auto-generated. Regenerate: python scripts/gen_index.py -->
```

Generated files should avoid volatile content such as commit hash, dirty/clean state, timestamps, or machine-specific paths unless explicitly requested.

## Change Gate

Before code changes:

1. Read standing rules.
2. Build a fact chain.
3. Check callers with search.
4. Write or identify the failing test for behavior changes.
5. Plan doc for high-risk paths.

After code changes:

1. Run targeted tests.
2. Run formatting/compile/import checks as appropriate.
3. Regenerate indexes.
4. Update docs in the correct class.
5. Ensure `git status --short` is explainable.

