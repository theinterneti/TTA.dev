"""TTA.dev CLI: `tta new <app-name>` — opinionated project scaffolding.

Creates a minimal but fully-working TTA.dev project in a new directory:

    my-app/
    ├── pyproject.toml       # uv project, depends on ttadev
    ├── README.md            # brief usage instructions
    ├── main.py              # minimal async main with LambdaPrimitive
    └── tests/
        └── test_main.py     # one passing smoke test

Usage::

    tta new my-app
    tta new my-app --output-dir ~/projects
    tta new my-app --no-git
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------

#: Only alphanumeric characters, hyphens, and underscores are valid.
_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")


def validate_app_name(name: str) -> str | None:
    """Validate *name* as a TTA.dev app name.

    Args:
        name: Candidate app name.

    Returns:
        An error message string if invalid, or ``None`` if the name is
        acceptable.
    """
    if not name:
        return "App name must not be empty."
    if not _VALID_NAME_RE.match(name):
        return (
            f"Invalid app name {name!r}. "
            "Use only letters, digits, hyphens (-) and underscores (_), "
            "starting with a letter or digit."
        )
    return None


# ---------------------------------------------------------------------------
# Scaffold templates
# ---------------------------------------------------------------------------

_PYPROJECT_TOML = """\
[project]
name = "{app_name}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["ttadev"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""

_README_MD = """\
# {app_name}

Built with [TTA.dev](https://tta.dev) — workflow primitives for AI agents.

## Quick start

```bash
uv run python main.py
```

## Run tests

```bash
uv run pytest
```

## Learn more

- [TTA.dev docs](https://tta.dev/docs)
- [Primitive catalog](https://tta.dev/docs/primitives)
"""

_MAIN_PY = '''\
"""{app_name} — built with TTA.dev primitives."""
import asyncio
from ttadev.primitives import LambdaPrimitive, WorkflowContext


async def process(data: str, ctx: WorkflowContext) -> str:
    """Replace this with your actual logic."""
    return f"Processed: {data}"


async def main() -> None:
    workflow = LambdaPrimitive(process)
    ctx = WorkflowContext(workflow_id="{app_name}-run")
    result = await workflow.execute("Hello, TTA.dev!", ctx)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
'''

_TEST_MAIN_PY = """\
import pytest
from ttadev.primitives import WorkflowContext
from main import process


@pytest.mark.asyncio
async def test_process_returns_string() -> None:
    ctx = WorkflowContext(workflow_id="test")
    result = await process("input", ctx)
    assert isinstance(result, str)
    assert "input" in result
"""


def _render(template: str, app_name: str) -> str:
    """Substitute ``{app_name}`` in *template*.

    Args:
        template: A string template with ``{app_name}`` placeholders.
        app_name: The application name to substitute.

    Returns:
        The rendered string.
    """
    return template.replace("{app_name}", app_name)


# ---------------------------------------------------------------------------
# File creation helpers
# ---------------------------------------------------------------------------


def _write_scaffold(app_dir: Path, app_name: str) -> list[Path]:
    """Write all scaffold files under *app_dir*.

    Args:
        app_dir: Root directory of the new application (must not exist yet).
        app_name: Application name used for template substitution.

    Returns:
        List of ``Path`` objects for every file that was written.
    """
    files: list[tuple[Path, str]] = [
        (app_dir / "pyproject.toml", _render(_PYPROJECT_TOML, app_name)),
        (app_dir / "README.md", _render(_README_MD, app_name)),
        (app_dir / "main.py", _render(_MAIN_PY, app_name)),
        (app_dir / "tests" / "test_main.py", _render(_TEST_MAIN_PY, app_name)),
    ]

    written: list[Path] = []
    for path, content in files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)

    return written


# ---------------------------------------------------------------------------
# git init helper
# ---------------------------------------------------------------------------


def _git_init(app_dir: Path) -> bool:
    """Run ``git init`` inside *app_dir*.

    Args:
        app_dir: Directory in which to run ``git init``.

    Returns:
        ``True`` if the command succeeded, ``False`` otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "init"],
            cwd=app_dir,
            capture_output=True,
        )
        return result.returncode == 0
    except (OSError, FileNotFoundError):
        return False


# ---------------------------------------------------------------------------
# Public command entry point
# ---------------------------------------------------------------------------


def cmd_new(
    args: object,
    *,
    project_root: Path = Path("."),
) -> int:
    """Implement ``tta new <app-name>``.

    Validates the app name, creates the directory structure, writes scaffold
    files, and optionally runs ``git init``.

    Args:
        args: Parsed CLI args.  Expected attributes:

            * ``name`` (str) — app name
            * ``output_dir`` (str | None) — parent directory (default: CWD)
            * ``no_git`` (bool) — skip ``git init`` when ``True``

        project_root: Unused; kept for API symmetry with other CLI commands.

    Returns:
        0 on success, 1 on any error.
    """
    app_name: str = getattr(args, "name", "")
    raw_output_dir: str | None = getattr(args, "output_dir", None)
    no_git: bool = getattr(args, "no_git", False)

    # ------------------------------------------------------------------ #
    # 1. Validate name                                                     #
    # ------------------------------------------------------------------ #
    error = validate_app_name(app_name)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------ #
    # 2. Resolve output directory                                          #
    # ------------------------------------------------------------------ #
    parent_dir = Path(raw_output_dir) if raw_output_dir else Path.cwd()
    app_dir = parent_dir / app_name

    if app_dir.exists():
        print(
            f"error: directory {app_dir} already exists. Remove it or choose a different name.",
            file=sys.stderr,
        )
        return 1

    # ------------------------------------------------------------------ #
    # 3. Write scaffold                                                    #
    # ------------------------------------------------------------------ #
    try:
        written = _write_scaffold(app_dir, app_name)
    except OSError as exc:
        print(f"error: could not create project files: {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------ #
    # 4. Optionally run git init                                           #
    # ------------------------------------------------------------------ #
    git_ok = False
    if not no_git:
        git_ok = _git_init(app_dir)

    # ------------------------------------------------------------------ #
    # 5. Success message                                                   #
    # ------------------------------------------------------------------ #
    print(f"\n✅  Created {app_name}/ with {len(written)} files:\n")
    for path in written:
        rel = path.relative_to(app_dir)
        print(f"   {app_name}/{rel}")

    if not no_git:
        if git_ok:
            print("\n   Initialised empty Git repository.")
        else:
            print("\n   ⚠  git init failed — you can run it manually.")

    print("\n🚀  Next steps:\n")
    try:
        cd_target = app_dir.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        cd_target = app_dir.resolve()
    print(f"   cd {cd_target}")
    print("   uv run python main.py")
    print("   uv run pytest\n")

    return 0
