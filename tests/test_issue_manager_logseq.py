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


def test_generate_logseq_todo_basic(monkeypatch) -> None:
    manager = IssueManager()

    issue = _make_issue(labels=["P2"], state="OPEN")
    monkeypatch.setattr(manager, "get_issue", lambda n: issue)

    block = manager.generate_logseq_todo(issue.number)
    assert block is not None

    lines = block.splitlines()

    # First line is a TODO with dev tag
    assert lines[0].startswith("- TODO Implement CachePrimitive metrics")
    assert "#dev-todo" in lines[0]

    # Default type and mapped priority
    assert "type:: implementation" in block
    assert "priority:: medium" in block  # from P2

    # Status is lowercased
    assert "status:: open" in block

    # URL includes repo and issue number
    assert re.search(r"url:: https://github.com/.+/issues/42", block)


def test_generate_logseq_todo_with_labels_and_milestone(monkeypatch) -> None:
    manager = IssueManager()

    issue = _make_issue(
        labels=["P0", "observability"],
        state="OPEN",
        milestone="Phase 2: Observability Integration",
        assignees=["theinterneti"],
    )
    monkeypatch.setattr(manager, "get_issue", lambda n: issue)

    block = manager.generate_logseq_todo(issue.number)
    assert block is not None

    lines = block.splitlines()

    # Tags include non-priority labels only
    assert "#observability" in lines[0]
    assert "#P0" not in lines[0]

    # Priority and type reflect labels
    assert "priority:: high" in block  # P0
    assert "type:: observability" in block

    # Milestone and assignee lines present
    assert "milestone:: [[Phase 2: Observability Integration]]" in block
    assert "assigned:: [[@theinterneti]]" in block


def test_generate_logseq_todo_returns_none_for_missing_issue(monkeypatch) -> None:
    manager = IssueManager()
    monkeypatch.setattr(manager, "get_issue", lambda n: None)

    block = manager.generate_logseq_todo(9999)
    assert block is None
