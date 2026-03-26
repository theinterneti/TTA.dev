"""ProjectSession — shared context grouping multiple agent sessions.

Storage layout:
  .tta/projects/{name}.json  — project metadata (name-addressed for easy lookup)

A ProjectSession is identified by its human-readable name (e.g. "pr-223-review").
Multiple agent processes join the same project by name; each adds themselves to
member_agent_ids.  Role assignments map role names to the agent_id holding them.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ProjectSession:
    """Shared context grouping multiple agent sessions under one project."""

    id: str
    name: str  # human-readable slug, e.g. "pr-223-review"
    created_at: str  # ISO 8601
    project_path: str
    member_agent_ids: list[str] = field(default_factory=list)
    role_assignments: dict[str, str] = field(default_factory=dict)  # role → agent_id


class ProjectSessionManager:
    """Manages project session lifecycle and membership."""

    def __init__(self, data_dir: Path | str = ".tta") -> None:
        self._projects_dir = Path(data_dir) / "projects"
        self._projects_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def create(self, name: str) -> ProjectSession:
        """Create a new project session. Raises if name already exists."""
        proj = ProjectSession(
            id=str(uuid.uuid4()),
            name=name,
            created_at=datetime.now(UTC).isoformat(),
            project_path=str(Path.cwd()),
        )
        self._persist(proj)
        return proj

    def join(self, name: str) -> ProjectSession:
        """Return the existing project for *name*, or create it if absent."""
        existing = self.get(name)
        if existing is not None:
            return existing
        return self.create(name)

    def get(self, name: str) -> ProjectSession | None:
        """Return the project for *name*, or None if it doesn't exist."""
        path = self._projects_dir / f"{name}.json"
        if not path.exists():
            return None
        try:
            return ProjectSession(**json.loads(path.read_text()))
        except Exception:
            return None

    def get_by_id(self, project_id: str) -> ProjectSession | None:
        """Return a project by its durable ID, or None if it doesn't exist."""
        return self._get_by_id(project_id)

    def list(self) -> list[ProjectSession]:
        """Return all projects newest-first."""
        projects: list[ProjectSession] = []
        for f in self._projects_dir.glob("*.json"):
            try:
                projects.append(ProjectSession(**json.loads(f.read_text())))
            except Exception:
                continue
        projects.sort(key=lambda p: p.created_at, reverse=True)
        return projects

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    def add_member(self, project_id: str, agent_id: str) -> None:
        """Add agent_id to the project's member list (idempotent)."""
        proj = self._get_by_id(project_id)
        if proj is None:
            return
        if agent_id not in proj.member_agent_ids:
            proj.member_agent_ids.append(agent_id)
            self._persist(proj)

    def assign_role(self, project_id: str, role: str, agent_id: str) -> None:
        """Assign a role to an agent within the project."""
        proj = self._get_by_id(project_id)
        if proj is None:
            return
        proj.role_assignments[role] = agent_id
        self._persist(proj)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _persist(self, proj: ProjectSession) -> None:
        path = self._projects_dir / f"{proj.name}.json"
        path.write_text(json.dumps(asdict(proj), indent=2))

    def _get_by_id(self, project_id: str) -> ProjectSession | None:
        for f in self._projects_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                if data.get("id") == project_id:
                    return ProjectSession(**data)
            except Exception:
                continue
        return None
