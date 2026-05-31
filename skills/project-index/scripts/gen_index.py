#!/usr/bin/env python3
"""
gen_index.py - Two-tier project index for AI-assisted development.

Tier 1 (OVERVIEW): ~2K tokens. Module map, key symbols, deps.
Tier 2 (API DETAIL): On-demand sections per module with full signatures.

AI reads Tier 1 first, then jumps to specific Tier 2 sections when needed.
Uses Python stdlib only. No external dependencies.

Usage:
    python3 scripts/gen_index.py              # Generate PROJECT_INDEX.md in project root
    python3 scripts/gen_index.py --if-stale   # Only regenerate if source files changed
    python3 scripts/gen_index.py --stdout     # Print to stdout
    python3 scripts/gen_index.py --with-status # Include transient git status hints
"""

import ast
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_EXTENSIONS = {".py"}

CONFIG_EXTENSIONS = {".yaml", ".yml", ".toml", ".json"}

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build",
    ".tox", ".eggs", ".claude", ".cursor", ".idea", ".vscode",
    "legacy",         # archived old system; not active runtime
    "data",           # runtime state and trade history
    "logs",           # runtime logs
    ".mypy_cache",
    ".ruff_cache",
}

IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Pipfile.lock", "requirements.txt",
    ".DS_Store",
    "_analyze.py", "_test_import.py", "_tmp_pnl_report.py",
    "_verify_import.py", "_test_bms.py", "_import_test.py",
}

MAX_API_ENTRIES_PER_FILE = 10
MAX_FILES = 260

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_git_root():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except Exception:
        return Path.cwd()


def get_recent_commits(n=8):
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_branch_info():
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_git_status_summary():
    """Get changed files grouped by area."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True,
        )
    except Exception:
        return "", {}

    lines = result.stdout.splitlines()
    is_dirty = len(lines) > 0
    areas = defaultdict(int)
    for line in lines:
        path = line[3:].strip().split("/")[0] if len(line) > 3 else ""
        if path:
            areas[path] += 1
    return "dirty" if is_dirty else "clean", dict(areas)


def should_ignore(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    for part in rel.parts:
        if part in IGNORE_DIRS or part.endswith(".egg-info"):
            return True
    if rel.name in IGNORE_FILES:
        return True
    return False


def collect_files(root: Path):
    all_exts = SOURCE_EXTENSIONS | CONFIG_EXTENSIONS
    files = []
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in all_exts and not should_ignore(f, root):
            files.append(f)
        if len(files) >= MAX_FILES:
            break
    files.sort(key=lambda f: str(f.relative_to(root)))
    return files


def _is_test_file(rel_path: str) -> bool:
    parts = rel_path.split("/")
    return any(p.startswith("test") for p in parts)


# ---------------------------------------------------------------------------
# Python analysis (ast-based)
# ---------------------------------------------------------------------------


def format_arg(arg_node):
    name = arg_node.arg
    if name in ("self", "cls"):
        return None
    ann = ""
    if arg_node.annotation:
        try:
            ann = ": " + ast.unparse(arg_node.annotation)
        except Exception:
            pass
    return f"{name}{ann}"


def format_func_sig(node):
    args = [a for a in (format_arg(a) for a in node.args.args) if a]
    ret = ""
    if node.returns:
        try:
            ret = " -> " + ast.unparse(node.returns)
        except Exception:
            pass
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}{node.name}({', '.join(args)}){ret}"


def _extract_dataclass_fields(class_node):
    """Extract fields from a @dataclass class via annotated assignments."""
    fields = []
    for item in class_node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            name = item.target.id
            try:
                ann = ast.unparse(item.annotation)
            except Exception:
                ann = "?"
            default = ""
            if item.value is not None:
                try:
                    default = f" = {ast.unparse(item.value)}"
                except Exception:
                    default = " = ..."
            fields.append(f"{name}: {ann}{default}")
    return fields


def _is_dataclass(class_node):
    """Check if a class has @dataclass decorator."""
    for dec in class_node.decorator_list:
        name = ""
        if isinstance(dec, ast.Name):
            name = dec.id
        elif isinstance(dec, ast.Attribute):
            name = dec.attr
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                name = dec.func.id
            elif isinstance(dec.func, ast.Attribute):
                name = dec.func.attr
        if name == "dataclass":
            return True
    return False


def analyze_python(filepath: Path):
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except Exception:
        return None

    info = {
        "docstring": ast.get_docstring(tree) or "",
        "classes": [],
        "functions": [],
        "imports_from": [],
    }

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = item.name
                    is_public = not name.startswith("_")
                    is_init = name == "__init__"
                    is_key_private = (
                        name.startswith("_")
                        and not name.startswith("__")
                        and not name.endswith("__")
                    )
                    if is_public or is_init or is_key_private:
                        methods.append(format_func_sig(item))
            cls_info = {
                "name": node.name,
                "doc": (ast.get_docstring(node) or "").split("\n")[0],
                "methods": methods,
            }
            if _is_dataclass(node):
                cls_info["fields"] = _extract_dataclass_fields(node)
            info["classes"].append(cls_info)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            is_public = not name.startswith("_")
            is_key_private = (
                name.startswith("_")
                and not name.startswith("__")
            )
            if is_public or is_key_private:
                info["functions"].append({
                    "sig": format_func_sig(node),
                    "doc": (ast.get_docstring(node) or "").split("\n")[0],
                })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                info["imports_from"].append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                info["imports_from"].append(node.module.split(".")[0])

    return info


def analyze_file(filepath: Path):
    ext = filepath.suffix
    if ext == ".py":
        return ("python", analyze_python(filepath))
    else:
        return ("generic", None)


# ---------------------------------------------------------------------------
# Dependency graph
# ---------------------------------------------------------------------------


def build_dep_graph(py_results, root: Path):
    internal = set()
    for fp in py_results:
        rel = fp.relative_to(root)
        internal.add(rel.parts[0].replace(".py", ""))
    graph = defaultdict(set)
    for fp, info in py_results.items():
        rel = str(fp.relative_to(root))
        for imp in info.get("imports_from", []):
            if imp in internal:
                graph[rel].add(imp)
    return graph


# ---------------------------------------------------------------------------
# Group files by module directory
# ---------------------------------------------------------------------------


def group_by_module(files, root):
    """Group files into modules (directories or root-level files)."""
    modules = defaultdict(list)
    for f in files:
        rel = f.relative_to(root)
        if len(rel.parts) == 1:
            modules["(root)"].append(f)
        else:
            modules[rel.parts[0]].append(f)
    return dict(modules)


# ---------------------------------------------------------------------------
# TIER 1: Compact overview (~2K tokens)
# ---------------------------------------------------------------------------


def generate_tier1(root, files, results, py_results, dep_graph, include_status=False):
    """Generate compact overview section."""
    lines = []
    lines.append("# PROJECT INDEX")
    lines.append("<!-- Auto-generated. Regenerate: python3 scripts/gen_index.py -->")
    lines.append("<!-- Tier 1 (overview) ends at the '---' separator. -->")
    lines.append(
        "<!-- Read only Tier 1 first. Jump to Tier 2 sections when you need API details. -->"
    )
    lines.append("")

    # Project name + summary
    lines.append(f"## {root.name}")
    _add_readme_summary(lines, root)

    changed_areas = {}
    if include_status:
        branch = get_branch_info()
        tree_status, changed_areas = get_git_status_summary()
        if branch:
            lines.append(f"**Branch:** `{branch}` | **Tree:** `{tree_status}`")
            lines.append("")

    # Module map (compact table)
    modules = group_by_module(files, root)
    lines.append("## Modules")
    lines.append("")
    lines.append("| Module | Purpose | Key Files & Types |")
    lines.append("|--------|---------|-------------------|")

    for mod_name in sorted(modules.keys()):
        mod_files = modules[mod_name]
        src_files = [
            f for f in mod_files
            if f.suffix in SOURCE_EXTENSIONS
            and not _is_test_file(str(f.relative_to(root)))
            and f.name != "__init__.py"
        ]
        if not src_files and mod_name != "(root)":
            continue

        purpose = ""
        file_type_pairs = []
        for f in sorted(src_files, key=lambda x: x.name):
            if f not in results:
                continue
            lang, info = results[f]
            rel = str(f.relative_to(root))
            if lang == "python" and info:
                if not purpose and info.get("docstring"):
                    purpose = info["docstring"].split("\n")[0][:60]
                types_in_file = []
                for c in info.get("classes", []):
                    types_in_file.append(c["name"])
                for fn in info.get("functions", []):
                    name = fn["sig"].split("(")[0]
                    if not name.startswith("_"):
                        types_in_file.append(name + "()")
                if types_in_file:
                    file_type_pairs.append(
                        f"`{f.name}`: {', '.join(types_in_file[:3])}"
                        + (f" +{len(types_in_file) - 3}" if len(types_in_file) > 3 else "")
                    )
                else:
                    file_type_pairs.append(f"`{f.name}`")

        entries_str = "; ".join(file_type_pairs[:4])
        if len(file_type_pairs) > 4:
            entries_str += f"; +{len(file_type_pairs) - 4} more"

        display = mod_name if mod_name != "(root)" else "(root)"
        lines.append(f"| `{display}` | {purpose} | {entries_str} |")

    # Test summary
    test_count = sum(1 for f in files if _is_test_file(str(f.relative_to(root))))
    if test_count:
        lines.append(f"| `tests/` | {test_count} | Unit & integration tests | - |")
    lines.append("")

    # Key symbols registry (compact: just names grouped by domain)
    lines.append("## Key Symbols")
    lines.append("")
    symbol_groups = defaultdict(list)

    for f, info in py_results.items():
        rel = str(f.relative_to(root))
        if _is_test_file(rel):
            continue
        mod = rel.split("/")[0] if "/" in rel else "(root)"
        for c in info.get("classes", []):
            symbol_groups[mod].append(c["name"])
        for fn in info.get("functions", []):
            name = fn["sig"].split("(")[0]
            if not name.startswith("_"):
                symbol_groups[mod].append(name + "()")

    for mod in sorted(symbol_groups.keys()):
        syms = symbol_groups[mod]
        if syms:
            display = ", ".join(syms[:12])
            if len(syms) > 12:
                display += f" +{len(syms) - 12}"
            lines.append(f"- **{mod}**: {display}")
    lines.append("")

    # Dependencies (compact)
    if dep_graph:
        mod_deps = defaultdict(set)
        for src, deps in dep_graph.items():
            src_mod = src.split("/")[0] if "/" in src else src
            for d in deps:
                if d != src_mod.replace(".py", ""):
                    mod_deps[src_mod].add(d)
        if mod_deps:
            lines.append("## Dependencies")
            lines.append("```")
            for src, deps in sorted(mod_deps.items()):
                lines.append(f"  {src} -> {', '.join(sorted(deps))}")
            lines.append("```")
            lines.append("")

    # Change hints
    if changed_areas:
        lines.append("## Active Changes")
        top_areas = sorted(changed_areas.items(), key=lambda x: -x[1])[:8]
        for area, count in top_areas:
            lines.append(f"- `{area}`: {count} changed")
        lines.append("")

    # Reading guide
    lines.append("## Reading Guide")
    lines.append("- Read this overview first (~2K tokens).")
    lines.append("- Jump to a **Tier 2** section below only when you need method signatures.")
    lines.append("- Pick one module at a time; read at most 3 source files before expanding scope.")
    lines.append("- When modifying a function, check all files that import this module.")
    lines.append("")

    return lines


# ---------------------------------------------------------------------------
# TIER 2: Detailed API sections (on-demand, per module)
# ---------------------------------------------------------------------------


def generate_tier2(root, files, results, py_results):
    """Generate detailed API sections, one per module."""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("# Tier 2: API Detail")
    lines.append("<!-- Read only the section for the module you're working on. -->")
    lines.append("")

    modules = group_by_module(files, root)

    for mod_name in sorted(modules.keys()):
        mod_files = modules[mod_name]
        has_api = False
        for f in mod_files:
            rel = str(f.relative_to(root))
            if _is_test_file(rel):
                continue
            if f in py_results:
                info = py_results[f]
                if info.get("classes") or info.get("functions"):
                    has_api = True
                    break

        if not has_api:
            continue

        display = mod_name if mod_name != "(root)" else "Root Files"
        lines.append(f"## {display}")
        lines.append("")

        for f in sorted(mod_files, key=lambda x: str(x)):
            rel = str(f.relative_to(root))
            if _is_test_file(rel):
                continue
            if rel.endswith("__init__.py"):
                continue

            if f in py_results:
                info = py_results[f]
                if not info["classes"] and not info["functions"]:
                    continue
                lines.append(f"### `{rel}`")
                if info["docstring"]:
                    lines.append(info["docstring"].split("\n")[0])
                lines.append("")
                for cls in info["classes"]:
                    lines.append(f"- **class {cls['name']}** {cls['doc']}")
                    if cls.get("fields"):
                        lines.append(f"  - Fields: {', '.join(f'`{f}`' for f in cls['fields'][:10])}")
                        if len(cls["fields"]) > 10:
                            lines.append(f"    +{len(cls['fields']) - 10} more fields")
                    for m in cls["methods"][:12]:
                        lines.append(f"  - `{m}`")
                    if len(cls["methods"]) > 12:
                        lines.append(f"  - ... +{len(cls['methods']) - 12} more")
                for func in info["functions"]:
                    lines.append(f"- `{func['sig']}`")
                    if func["doc"]:
                        lines.append(f"  {func['doc']}")
                lines.append("")

    return lines


# ---------------------------------------------------------------------------
# Generate the full index
# ---------------------------------------------------------------------------


def generate_index(root: Path, include_status=False) -> str:
    files = collect_files(root)
    if not files:
        return "# PROJECT INDEX\n\nNo source files found.\n"

    results = {}
    for f in files:
        lang, info = analyze_file(f)
        if info:
            results[f] = (lang, info)

    py_results = {f: info for f, (lang, info) in results.items() if lang == "python"}
    dep_graph = build_dep_graph(py_results, root)

    tier1 = generate_tier1(root, files, results, py_results, dep_graph, include_status=include_status)
    tier2 = generate_tier2(root, files, results, py_results)

    return "\n".join(tier1 + tier2)


def _add_readme_summary(lines, root):
    for name in ("README.md", "README.rst", "README.txt", "README"):
        readme = root / name
        if readme.exists():
            try:
                content = readme.read_text(encoding="utf-8", errors="replace")
                for para in content.split("\n\n"):
                    stripped = para.strip().strip("#").strip()
                    if stripped and not stripped.startswith(("![", "[!", "<!--", "```", "---")):
                        lines.append(f"> {stripped[:300]}")
                        lines.append("")
                        return
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate two-tier PROJECT_INDEX.md for AI-assisted development"
    )
    parser.add_argument("--root", default=None, help="Project root directory")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout")
    parser.add_argument(
        "--if-stale", action="store_true",
        help="Skip if index is newer than all source files",
    )
    parser.add_argument(
        "--with-status", action="store_true",
        help="Include transient git branch/tree status and active change hints",
    )
    args = parser.parse_args()

    root = Path(args.root) if args.root else get_git_root()
    index_path = Path(args.output) if args.output else root / "PROJECT_INDEX.md"

    # Staleness check
    if args.if_stale and index_path.exists():
        idx_mtime = index_path.stat().st_mtime
        stale = False
        for ext in SOURCE_EXTENSIONS | CONFIG_EXTENSIONS:
            for f in root.rglob(f"*{ext}"):
                if not should_ignore(f, root) and f.stat().st_mtime > idx_mtime:
                    stale = True
                    break
            if stale:
                break
        if not stale:
            print("Index up to date.", file=sys.stderr)
            sys.exit(0)

    content = generate_index(root, include_status=args.with_status)

    if args.stdout:
        print(content)
    else:
        index_path.write_text(content, encoding="utf-8")
        sep = content.find("\n---\n")
        if sep > 0:
            t1_chars = sep
            t2_chars = len(content) - sep
            print(
                f"Generated {index_path} ({content.count(chr(10))} lines) | "
                f"Tier 1: ~{t1_chars // 4} tokens | Tier 2: ~{t2_chars // 4} tokens",
                file=sys.stderr,
            )
        else:
            print(f"Generated {index_path} ({content.count(chr(10))} lines)", file=sys.stderr)


if __name__ == "__main__":
    main()
