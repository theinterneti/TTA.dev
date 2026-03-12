"""tta project subcommands: join, list, show."""

from __future__ import annotations

import json
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

_SAFE_NAME = re.compile(r"^[A-Za-z0-9_\-]+$")


def _validate_name(name: str) -> None:
    """Reject names that could escape the projects directory."""
    if not _SAFE_NAME.match(name):
        print(
            f"Invalid project name {name!r}. Use only letters, digits, hyphens, underscores.",
            file=sys.stderr,
        )
        sys.exit(1)


def _projects_dir(data_dir: Path) -> Path:
    d = data_dir / "projects"
    d.mkdir(parents=True, exist_ok=True)
    return d


def join(name: str, data_dir: Path) -> None:
    """Join (or re-join) a project by name."""
    _validate_name(name)
    projects = _projects_dir(data_dir)
    project_file = projects / f"{name}.json"

    if project_file.exists():
        meta = json.loads(project_file.read_text())
    else:
        meta = {
            "id": str(uuid.uuid4()),
            "name": name,
            "created_at": datetime.now(UTC).isoformat(),
        }
        project_file.write_text(json.dumps(meta, indent=2))

    # Write current project pointer
    (data_dir / "current_project").write_text(meta["id"])

    print(f"Joined project: {name}")
    print(f"export TTA_PROJECT_ID={meta['id']}")


def list_projects(data_dir: Path) -> None:
    """List all known projects."""
    projects = _projects_dir(data_dir)
    files = sorted(projects.glob("*.json"))
    if not files:
        print("No projects found.")
        return
    for f in files:
        try:
            meta = json.loads(f.read_text())
            print(f"{meta['name']}  ({meta['id']})")
        except Exception:
            continue


def show(name: str, data_dir: Path) -> None:
    """Show details for a named project."""
    _validate_name(name)
    project_file = _projects_dir(data_dir) / f"{name}.json"
    if not project_file.exists():
        print(f"Project not found: {name}", file=sys.stderr)
        sys.exit(1)
    meta = json.loads(project_file.read_text())
    print(f"Project: {meta['name']}")
    print(f"  id:         {meta['id']}")
    print(f"  created_at: {meta['created_at']}")
