"""Tests for Session Group Primitive."""

import json

import pytest

from tta_dev_primitives.session_group import (
    GroupStatus,
    SessionGroupPrimitive,
)


@pytest.fixture
def temp_storage(tmp_path):
    """Fixture providing temporary storage path."""
    return tmp_path / "session_groups.json"


@pytest.fixture
def session_groups(temp_storage):
    """Fixture providing session group primitive with temp storage."""
    return SessionGroupPrimitive(storage_path=temp_storage)


def test_session_group_initialization(session_groups, temp_storage):
    """Test session group primitive initializes correctly."""
    assert session_groups.storage_path == temp_storage
    assert len(session_groups.groups) == 0
    assert len(session_groups.session_to_groups) == 0


def test_create_group(session_groups):
    """Test creating a new group."""
    group = session_groups.create_group(
        group_id="feature-auth",
        description="Authentication feature",
        tags=["feature", "backend"],
    )

    assert group.group_id == "feature-auth"
    assert group.description == "Authentication feature"
    assert group.tags == ["feature", "backend"]
    assert group.status == GroupStatus.ACTIVE
    assert group.is_active()
    assert len(group.session_ids) == 0


def test_create_duplicate_group(session_groups):
    """Test creating duplicate group raises error."""
    session_groups.create_group("feature-auth", "Auth feature")

    with pytest.raises(ValueError, match="already exists"):
        session_groups.create_group("feature-auth", "Duplicate")


def test_add_session_to_group(session_groups):
    """Test adding sessions to a group."""
    session_groups.create_group("feature-auth", "Auth feature")

    session_groups.add_session_to_group("session-001", "feature-auth")
    session_groups.add_session_to_group("session-002", "feature-auth")

    group = session_groups.get_group("feature-auth")
    assert len(group.session_ids) == 2
    assert "session-001" in group.session_ids
    assert "session-002" in group.session_ids


def test_add_session_to_nonexistent_group(session_groups):
    """Test adding session to nonexistent group raises error."""
    with pytest.raises(ValueError, match="does not exist"):
        session_groups.add_session_to_group("session-001", "nonexistent")


def test_add_duplicate_session_to_group(session_groups):
    """Test adding duplicate session to group raises error."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.add_session_to_group("session-001", "feature-auth")

    with pytest.raises(ValueError, match="already in group"):
        session_groups.add_session_to_group("session-001", "feature-auth")


def test_remove_session_from_group(session_groups):
    """Test removing session from a group."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.add_session_to_group("session-001", "feature-auth")
    session_groups.add_session_to_group("session-002", "feature-auth")

    session_groups.remove_session_from_group("session-001", "feature-auth")

    group = session_groups.get_group("feature-auth")
    assert len(group.session_ids) == 1
    assert "session-002" in group.session_ids
    assert "session-001" not in group.session_ids


def test_remove_session_from_nonexistent_group(session_groups):
    """Test removing session from nonexistent group raises error."""
    with pytest.raises(ValueError, match="does not exist"):
        session_groups.remove_session_from_group("session-001", "nonexistent")


def test_remove_nonexistent_session_from_group(session_groups):
    """Test removing nonexistent session from group raises error."""
    session_groups.create_group("feature-auth", "Auth feature")

    with pytest.raises(ValueError, match="not in group"):
        session_groups.remove_session_from_group("session-001", "feature-auth")


def test_get_group_sessions(session_groups):
    """Test getting all sessions in a group."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.add_session_to_group("session-001", "feature-auth")
    session_groups.add_session_to_group("session-002", "feature-auth")

    sessions = session_groups.get_group_sessions("feature-auth")
    assert len(sessions) == 2
    assert "session-001" in sessions
    assert "session-002" in sessions


def test_get_sessions_from_nonexistent_group(session_groups):
    """Test getting sessions from nonexistent group returns empty list."""
    sessions = session_groups.get_group_sessions("nonexistent")
    assert sessions == []


def test_get_session_groups(session_groups):
    """Test getting all groups a session belongs to."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.create_group("bug-fix", "Bug fixes")

    session_groups.add_session_to_group("session-001", "feature-auth")
    session_groups.add_session_to_group("session-001", "bug-fix")

    groups = session_groups.get_session_groups("session-001")
    assert len(groups) == 2
    assert "feature-auth" in groups
    assert "bug-fix" in groups


def test_get_groups_for_nonexistent_session(session_groups):
    """Test getting groups for nonexistent session returns empty list."""
    groups = session_groups.get_session_groups("nonexistent")
    assert groups == []


def test_list_all_groups(session_groups):
    """Test listing all groups."""
    session_groups.create_group("feature-auth", "Auth", ["feature"])
    session_groups.create_group("bug-fix", "Bugs", ["bug"])
    session_groups.create_group("refactor", "Refactoring", ["refactor"])

    groups = session_groups.list_groups()
    assert len(groups) == 3


def test_list_groups_by_tag(session_groups):
    """Test filtering groups by tag."""
    session_groups.create_group("feature-auth", "Auth", ["feature", "backend"])
    session_groups.create_group("feature-ui", "UI", ["feature", "frontend"])
    session_groups.create_group("bug-fix", "Bugs", ["bug"])

    feature_groups = session_groups.list_groups(filter_by_tag="feature")
    assert len(feature_groups) == 2

    bug_groups = session_groups.list_groups(filter_by_tag="bug")
    assert len(bug_groups) == 1


def test_list_groups_by_status(session_groups):
    """Test filtering groups by status."""
    session_groups.create_group("active-1", "Active group")
    session_groups.create_group("active-2", "Active group")
    session_groups.create_group("closed-1", "Closed group")
    session_groups.close_group("closed-1")

    active = session_groups.list_groups(status=GroupStatus.ACTIVE)
    assert len(active) == 2

    closed = session_groups.list_groups(status=GroupStatus.CLOSED)
    assert len(closed) == 1


def test_close_group(session_groups):
    """Test closing a group."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.close_group("feature-auth", summary="Feature completed")

    group = session_groups.get_group("feature-auth")
    assert group.status == GroupStatus.CLOSED
    assert group.summary == "Feature completed"
    assert group.closed_at is not None
    assert not group.is_active()


def test_close_nonexistent_group(session_groups):
    """Test closing nonexistent group raises error."""
    with pytest.raises(ValueError, match="does not exist"):
        session_groups.close_group("nonexistent")


def test_close_already_closed_group(session_groups):
    """Test closing already closed group raises error."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.close_group("feature-auth")

    with pytest.raises(ValueError, match="already closed"):
        session_groups.close_group("feature-auth")


def test_archive_group(session_groups):
    """Test archiving a group."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.archive_group("feature-auth")

    group = session_groups.get_group("feature-auth")
    assert group.status == GroupStatus.ARCHIVED


def test_archive_nonexistent_group(session_groups):
    """Test archiving nonexistent group raises error."""
    with pytest.raises(ValueError, match="does not exist"):
        session_groups.archive_group("nonexistent")


def test_delete_group(session_groups):
    """Test deleting a group."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.add_session_to_group("session-001", "feature-auth")

    session_groups.delete_group("feature-auth")

    assert session_groups.get_group("feature-auth") is None
    assert session_groups.get_session_groups("session-001") == []


def test_delete_nonexistent_group(session_groups):
    """Test deleting nonexistent group raises error."""
    with pytest.raises(ValueError, match="does not exist"):
        session_groups.delete_group("nonexistent")


def test_get_active_groups(session_groups):
    """Test getting only active groups."""
    session_groups.create_group("active-1", "Active")
    session_groups.create_group("active-2", "Active")
    session_groups.create_group("closed-1", "Closed")
    session_groups.close_group("closed-1")

    active = session_groups.get_active_groups()
    assert len(active) == 2
    assert all(g.is_active() for g in active)


def test_session_group_tags(session_groups):
    """Test session group tag operations."""
    group = session_groups.create_group("feature-auth", "Auth", ["feature"])

    assert group.has_tag("feature")
    assert not group.has_tag("bug")

    group.add_tag("backend")
    assert group.has_tag("backend")
    assert len(group.tags) == 2

    group.remove_tag("feature")
    assert not group.has_tag("feature")
    assert len(group.tags) == 1


def test_session_group_metadata(session_groups):
    """Test session group metadata storage."""
    group = session_groups.create_group(
        "feature-auth",
        "Auth feature",
        metadata={"priority": "high", "sprint": 42},
    )

    assert group.metadata["priority"] == "high"
    assert group.metadata["sprint"] == 42


def test_session_count(session_groups):
    """Test session count method."""
    session_groups.create_group("feature-auth", "Auth feature")
    session_groups.add_session_to_group("session-001", "feature-auth")
    session_groups.add_session_to_group("session-002", "feature-auth")

    group = session_groups.get_group("feature-auth")
    assert group.session_count() == 2


def test_summary_statistics(session_groups):
    """Test summary statistics."""
    session_groups.create_group("active-1", "Active", ["feature"])
    session_groups.create_group("active-2", "Active", ["bug"])
    session_groups.create_group("closed-1", "Closed", ["feature"])
    session_groups.close_group("closed-1")
    session_groups.add_session_to_group("session-001", "active-1")
    session_groups.add_session_to_group("session-002", "active-1")

    summary = session_groups.summary()
    assert summary["total_groups"] == 3
    assert summary["active_groups"] == 2
    assert summary["closed_groups"] == 1
    assert summary["total_sessions_tracked"] == 2
    assert "feature" in summary["unique_tags"]
    assert "bug" in summary["unique_tags"]


def test_persistence_save_and_load(temp_storage):
    """Test groups are saved and loaded correctly."""
    # Create and populate groups
    groups1 = SessionGroupPrimitive(storage_path=temp_storage)
    groups1.create_group("feature-auth", "Auth feature", ["feature"])
    groups1.add_session_to_group("session-001", "feature-auth")

    # Load in new instance
    groups2 = SessionGroupPrimitive(storage_path=temp_storage)
    group = groups2.get_group("feature-auth")

    assert group is not None
    assert group.description == "Auth feature"
    assert "feature" in group.tags
    assert "session-001" in group.session_ids


def test_persistence_file_format(temp_storage):
    """Test persistence file has expected format."""
    groups = SessionGroupPrimitive(storage_path=temp_storage)
    groups.create_group("feature-auth", "Auth feature")

    assert temp_storage.exists()

    with temp_storage.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert "groups" in data
    assert "version" in data
    assert "last_updated" in data
    assert len(data["groups"]) == 1
    assert data["groups"][0]["group_id"] == "feature-auth"


def test_reverse_index_rebuild(temp_storage):
    """Test reverse index is rebuilt on load."""
    # Create groups
    groups1 = SessionGroupPrimitive(storage_path=temp_storage)
    groups1.create_group("feature-auth", "Auth")
    groups1.create_group("bug-fix", "Bugs")
    groups1.add_session_to_group("session-001", "feature-auth")
    groups1.add_session_to_group("session-001", "bug-fix")

    # Load in new instance
    groups2 = SessionGroupPrimitive(storage_path=temp_storage)

    # Check reverse index
    session_groups = groups2.get_session_groups("session-001")
    assert len(session_groups) == 2
    assert "feature-auth" in session_groups
    assert "bug-fix" in session_groups


def test_multiple_sessions_multiple_groups(session_groups):
    """Test complex many-to-many session-group relationships."""
    # Create groups
    session_groups.create_group("feature-auth", "Auth")
    session_groups.create_group("feature-api", "API")
    session_groups.create_group("refactor", "Refactoring")

    # Add sessions to multiple groups
    session_groups.add_session_to_group("session-001", "feature-auth")
    session_groups.add_session_to_group("session-001", "refactor")

    session_groups.add_session_to_group("session-002", "feature-api")
    session_groups.add_session_to_group("session-002", "refactor")

    session_groups.add_session_to_group("session-003", "feature-auth")
    session_groups.add_session_to_group("session-003", "feature-api")

    # Verify relationships
    assert len(session_groups.get_session_groups("session-001")) == 2
    assert len(session_groups.get_session_groups("session-002")) == 2
    assert len(session_groups.get_session_groups("session-003")) == 2

    assert len(session_groups.get_group_sessions("feature-auth")) == 2
    assert len(session_groups.get_group_sessions("feature-api")) == 2
    assert len(session_groups.get_group_sessions("refactor")) == 2


def test_workflow_example_feature_development(session_groups):
    """Test realistic workflow: feature development over multiple sessions."""
    # Start feature work
    group = session_groups.create_group(
        "feature-payment",
        "Payment processing feature",
        tags=["feature", "backend", "critical"],
        metadata={"sprint": 42, "priority": "high"},
    )

    # Session 1: Initial planning
    session_groups.add_session_to_group("session-planning", "feature-payment")

    # Session 2-3: Implementation
    session_groups.add_session_to_group("session-impl-1", "feature-payment")
    session_groups.add_session_to_group("session-impl-2", "feature-payment")

    # Session 4: Bug fixes
    session_groups.add_session_to_group("session-bugfix", "feature-payment")

    # Session 5: Testing
    session_groups.add_session_to_group("session-testing", "feature-payment")

    # Verify state
    assert group.session_count() == 5

    # Complete feature
    session_groups.close_group(
        "feature-payment",
        summary="Payment feature completed, tested, and deployed",
    )

    # Verify closure
    closed_group = session_groups.get_group("feature-payment")
    assert closed_group.status == GroupStatus.CLOSED
    assert closed_group.summary is not None


def test_workflow_example_bug_investigation(session_groups):
    """Test realistic workflow: bug investigation across sessions."""
    # Create bug investigation group
    session_groups.create_group(
        "bug-memory-leak",
        "Memory leak in background worker",
        tags=["bug", "production", "urgent"],
    )

    # Add investigation sessions
    session_groups.add_session_to_group("debug-session-1", "bug-memory-leak")
    session_groups.add_session_to_group("debug-session-2", "bug-memory-leak")
    session_groups.add_session_to_group("fix-session", "bug-memory-leak")

    sessions = session_groups.get_group_sessions("bug-memory-leak")
    assert len(sessions) == 3

    # Close bug
    session_groups.close_group(
        "bug-memory-leak",
        summary="Memory leak fixed in worker cleanup logic",
    )

    bug_group = session_groups.get_group("bug-memory-leak")
    assert not bug_group.is_active()
