import re

from scripts.issue_manager import Issue, IssueManager


def _make_issue(
    *,
    number: int = 42,
    title: str = "Implement CachePrimitive metrics",
    body: str = "",
    labels: list[str] | None = None,
    state: str = "OPEN",
    milestone: str | None = None,
    assignees: list[str] | None = None,
) -> Issue:
    return Issue(
        number=number,
        title=title,
        body=body,
        labels=labels or [],
        state=state,
        milestone=milestone,
        assignees=assignees or [],
        created_at="2025-11-18T00:00:00Z",
        updated_at="2025-11-18T00:00:00Z",
    )


def test_generate_todo_block_basic(monkeypatch) -> None:
    # Arrange
    manager = IssueManager()
    issue = _make_issue(labels=["P2"], state="OPEN")
    monkeypatch.setattr(manager, "get_issue", lambda n: issue)

    # Act
    block = manager.generate_todo_block(issue.number)

    # Assert
    assert block is not None

    lines = block.splitlines()
    assert lines[0].startswith("- TODO Implement CachePrimitive metrics")
    assert "#dev-todo" in lines[0]
    assert "type:: implementation" in block
    assert "priority:: medium" in block
    assert "status:: open" in block
    assert re.search(r"url:: https://github.com/.+/issues/42", block)


def test_generate_todo_block_with_labels_and_milestone(monkeypatch) -> None:
    # Arrange
    manager = IssueManager()
    issue = _make_issue(
        labels=["P0", "observability"],
        state="OPEN",
        milestone="Phase 2: Observability Integration",
        assignees=["theinterneti"],
    )
    monkeypatch.setattr(manager, "get_issue", lambda n: issue)

    # Act
    block = manager.generate_todo_block(issue.number)

    # Assert
    assert block is not None

    lines = block.splitlines()
    assert "#observability" in lines[0]
    assert "#P0" not in lines[0]
    assert "priority:: high" in block
    assert "type:: observability" in block
    assert "milestone:: [[Phase 2: Observability Integration]]" in block
    assert "assigned:: [[@theinterneti]]" in block


def test_generate_todo_block_returns_none_for_missing_issue(monkeypatch) -> None:
    # Arrange
    manager = IssueManager()
    monkeypatch.setattr(manager, "get_issue", lambda n: None)

    # Act
    block = manager.generate_todo_block(9999)

    # Assert
    assert block is None
