"""Session Group Primitive.

This primitive enables synthetic grouping of related AI agent sessions for
better context engineering across multi-session workflows.

Example:
    >>> from tta_dev_primitives import SessionGroupPrimitive
    >>> groups = SessionGroupPrimitive()
    >>>
    >>> # Create a feature development group
    >>> groups.create_group(
    ...     group_id="feature-auth",
    ...     description="Authentication feature development",
    ...     tags=["feature", "auth", "backend"]
    ... )
    >>>
    >>> # Add sessions as they occur
    >>> groups.add_session_to_group("session-001", "feature-auth")
    >>> groups.add_session_to_group("session-002", "feature-auth")
    >>>
    >>> # Get all sessions in the group
    >>> sessions = groups.get_group_sessions("feature-auth")
    >>> print(f"Group has {len(sessions)} sessions")
    >>>
    >>> # Close group when feature is complete
    >>> groups.close_group("feature-auth", summary="Auth feature completed and tested")
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class GroupStatus(str, Enum):
    """Session group lifecycle status."""

    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


@dataclass
class SessionGroup:
    """Represents a group of related sessions.

    Attributes:
        group_id: Unique identifier for the group
        description: Human-readable description of the group purpose
        tags: List of tags for categorization and filtering
        session_ids: List of session IDs belonging to this group
        created_at: ISO timestamp of group creation
        status: Current lifecycle status
        closed_at: ISO timestamp when group was closed (if applicable)
        summary: Final summary when group is closed (if applicable)
        metadata: Additional metadata dictionary
    """

    group_id: str
    description: str
    tags: list[str] = field(default_factory=list)
    session_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: GroupStatus = GroupStatus.ACTIVE
    closed_at: str | None = None
    summary: str | None = None
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)

    def is_active(self) -> bool:
        """Check if group is active.

        Returns:
            True if group status is ACTIVE
        """
        return self.status == GroupStatus.ACTIVE

    def session_count(self) -> int:
        """Get number of sessions in group.

        Returns:
            Number of sessions
        """
        return len(self.session_ids)

    def has_tag(self, tag: str) -> bool:
        """Check if group has specific tag.

        Args:
            tag: Tag to check

        Returns:
            True if tag exists in group tags
        """
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        """Add tag to group.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove tag from group.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)


class SessionGroupPrimitive:
    """Manage synthetic grouping of related AI agent sessions.

    This primitive enables context engineering across multiple related sessions
    by grouping them under common identifiers (features, bugs, refactoring tasks).

    Attributes:
        storage_path: Path to session groups storage file
        groups: Dictionary of group_id -> SessionGroup
        session_to_groups: Reverse index of session_id -> list[group_id]

    Example:
        >>> groups = SessionGroupPrimitive()
        >>>
        >>> # Feature development workflow
        >>> groups.create_group("feature-auth", "Auth system", ["feature", "backend"])
        >>> groups.add_session_to_group("session-001", "feature-auth")
        >>> groups.add_session_to_group("session-002", "feature-auth")
        >>>
        >>> # Query group
        >>> sessions = groups.get_group_sessions("feature-auth")
        >>> print(f"Feature has {len(sessions)} sessions")
        >>>
        >>> # Close when complete
        >>> groups.close_group("feature-auth", "Feature deployed to production")
    """

    def __init__(self, storage_path: str | Path | None = None) -> None:
        """Initialize session group primitive.

        Args:
            storage_path: Path to groups storage file (default: .tta/session_groups.json)
        """
        self.storage_path = Path(storage_path or ".tta/session_groups.json")
        self.groups: dict[str, SessionGroup] = {}
        self.session_to_groups: dict[str, list[str]] = {}
        self._load_groups()

    def _load_groups(self) -> None:
        """Load session groups from storage."""
        if not self.storage_path.exists():
            return

        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Load groups
            for group_data in data.get("groups", []):
                group = SessionGroup(
                    group_id=group_data["group_id"],
                    description=group_data["description"],
                    tags=group_data.get("tags", []),
                    session_ids=group_data.get("session_ids", []),
                    created_at=group_data.get("created_at", datetime.now().isoformat()),
                    status=GroupStatus(group_data.get("status", "active")),
                    closed_at=group_data.get("closed_at"),
                    summary=group_data.get("summary"),
                    metadata=group_data.get("metadata", {}),
                )
                self.groups[group.group_id] = group

            # Build reverse index
            self._rebuild_session_index()

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            msg = f"Failed to load session groups from {self.storage_path}: {e}"
            raise RuntimeError(msg) from e

    def _save_groups(self) -> None:
        """Save session groups to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "groups": [asdict(group) for group in self.groups.values()],
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
        }

        with self.storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _rebuild_session_index(self) -> None:
        """Rebuild session-to-groups reverse index."""
        self.session_to_groups = {}
        for group in self.groups.values():
            for session_id in group.session_ids:
                if session_id not in self.session_to_groups:
                    self.session_to_groups[session_id] = []
                self.session_to_groups[session_id].append(group.group_id)

    def create_group(
        self,
        group_id: str,
        description: str,
        tags: list[str] | None = None,
        metadata: dict[str, str | int | float | bool] | None = None,
    ) -> SessionGroup:
        """Create a new session group.

        Args:
            group_id: Unique identifier for the group
            description: Human-readable description
            tags: Optional list of tags for categorization
            metadata: Optional metadata dictionary

        Returns:
            Created SessionGroup

        Raises:
            ValueError: If group_id already exists
        """
        if group_id in self.groups:
            msg = f"Group '{group_id}' already exists"
            raise ValueError(msg)

        group = SessionGroup(
            group_id=group_id,
            description=description,
            tags=tags or [],
            metadata=metadata or {},
        )

        self.groups[group_id] = group
        self._save_groups()
        return group

    def add_session_to_group(
        self,
        session_id: str,
        group_id: str,
    ) -> None:
        """Add a session to a group.

        A session can belong to multiple groups.

        Args:
            session_id: Session identifier to add
            group_id: Group identifier to add session to

        Raises:
            ValueError: If group doesn't exist or session already in group
        """
        if group_id not in self.groups:
            msg = f"Group '{group_id}' does not exist"
            raise ValueError(msg)

        group = self.groups[group_id]

        if session_id in group.session_ids:
            msg = f"Session '{session_id}' already in group '{group_id}'"
            raise ValueError(msg)

        # Add to group
        group.session_ids.append(session_id)

        # Update reverse index
        if session_id not in self.session_to_groups:
            self.session_to_groups[session_id] = []
        self.session_to_groups[session_id].append(group_id)

        self._save_groups()

    def remove_session_from_group(
        self,
        session_id: str,
        group_id: str,
    ) -> None:
        """Remove a session from a group.

        Args:
            session_id: Session identifier to remove
            group_id: Group identifier to remove session from

        Raises:
            ValueError: If group doesn't exist or session not in group
        """
        if group_id not in self.groups:
            msg = f"Group '{group_id}' does not exist"
            raise ValueError(msg)

        group = self.groups[group_id]

        if session_id not in group.session_ids:
            msg = f"Session '{session_id}' not in group '{group_id}'"
            raise ValueError(msg)

        # Remove from group
        group.session_ids.remove(session_id)

        # Update reverse index
        if session_id in self.session_to_groups:
            self.session_to_groups[session_id].remove(group_id)
            if not self.session_to_groups[session_id]:
                del self.session_to_groups[session_id]

        self._save_groups()

    def get_group(self, group_id: str) -> SessionGroup | None:
        """Get a session group by ID.

        Args:
            group_id: Group identifier

        Returns:
            SessionGroup or None if not found
        """
        return self.groups.get(group_id)

    def get_group_sessions(self, group_id: str) -> list[str]:
        """Get all session IDs in a group.

        Args:
            group_id: Group identifier

        Returns:
            List of session IDs (empty if group doesn't exist)
        """
        group = self.groups.get(group_id)
        return group.session_ids.copy() if group else []

    def get_session_groups(self, session_id: str) -> list[str]:
        """Get all groups a session belongs to.

        Args:
            session_id: Session identifier

        Returns:
            List of group IDs (empty if session not in any group)
        """
        return self.session_to_groups.get(session_id, []).copy()

    def list_groups(
        self,
        filter_by_tag: str | None = None,
        status: GroupStatus | None = None,
    ) -> list[SessionGroup]:
        """List all groups with optional filtering.

        Args:
            filter_by_tag: Optional tag to filter by
            status: Optional status to filter by

        Returns:
            List of SessionGroup objects matching filters
        """
        groups = list(self.groups.values())

        if filter_by_tag:
            groups = [g for g in groups if g.has_tag(filter_by_tag)]

        if status:
            groups = [g for g in groups if g.status == status]

        return groups

    def close_group(
        self,
        group_id: str,
        summary: str | None = None,
    ) -> None:
        """Close a session group.

        Args:
            group_id: Group identifier to close
            summary: Optional summary of group work

        Raises:
            ValueError: If group doesn't exist or is already closed
        """
        if group_id not in self.groups:
            msg = f"Group '{group_id}' does not exist"
            raise ValueError(msg)

        group = self.groups[group_id]

        if group.status == GroupStatus.CLOSED:
            msg = f"Group '{group_id}' is already closed"
            raise ValueError(msg)

        group.status = GroupStatus.CLOSED
        group.closed_at = datetime.now().isoformat()
        group.summary = summary

        self._save_groups()

    def archive_group(self, group_id: str) -> None:
        """Archive a session group.

        Archived groups are kept for historical reference but not shown in active lists.

        Args:
            group_id: Group identifier to archive

        Raises:
            ValueError: If group doesn't exist
        """
        if group_id not in self.groups:
            msg = f"Group '{group_id}' does not exist"
            raise ValueError(msg)

        group = self.groups[group_id]
        group.status = GroupStatus.ARCHIVED

        self._save_groups()

    def delete_group(self, group_id: str) -> None:
        """Delete a session group.

        This removes the group entirely from storage.

        Args:
            group_id: Group identifier to delete

        Raises:
            ValueError: If group doesn't exist
        """
        if group_id not in self.groups:
            msg = f"Group '{group_id}' does not exist"
            raise ValueError(msg)

        group = self.groups[group_id]

        # Remove from reverse index
        for session_id in group.session_ids:
            if session_id in self.session_to_groups:
                self.session_to_groups[session_id].remove(group_id)
                if not self.session_to_groups[session_id]:
                    del self.session_to_groups[session_id]

        # Remove group
        del self.groups[group_id]

        self._save_groups()

    def get_active_groups(self) -> list[SessionGroup]:
        """Get all active groups.

        Returns:
            List of active SessionGroup objects
        """
        return self.list_groups(status=GroupStatus.ACTIVE)

    def summary(self) -> dict[str, int | list[str]]:
        """Get summary statistics.

        Returns:
            Dictionary with group counts and statistics
        """
        active_groups = self.get_active_groups()
        all_tags = set()
        for group in self.groups.values():
            all_tags.update(group.tags)

        return {
            "total_groups": len(self.groups),
            "active_groups": len(active_groups),
            "closed_groups": len(self.list_groups(status=GroupStatus.CLOSED)),
            "archived_groups": len(self.list_groups(status=GroupStatus.ARCHIVED)),
            "total_sessions_tracked": len(self.session_to_groups),
            "unique_tags": sorted(all_tags),
        }
