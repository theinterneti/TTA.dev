"""Pydantic models for Dolt primitives."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DoltConfig(BaseModel):
    """Configuration for connecting to a Dolt repository.

    Args:
        repo_path: Filesystem path to the Dolt repository.
        host: Dolt SQL server host (for query operations).
        port: Dolt SQL server port.
        user: Dolt SQL server user.
        password: Dolt SQL server password.
        database: Dolt database name (defaults to repo directory name).
    """

    repo_path: str
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str | None = None

    def db_name(self) -> str:
        """Derive database name from repo path if not explicitly set."""
        if self.database:
            return self.database
        return self.repo_path.rstrip("/").split("/")[-1]


class BranchOperation(str, Enum):
    """Operations available on Dolt branches."""

    CREATE = "create"
    CHECKOUT = "checkout"
    CREATE_AND_CHECKOUT = "create_and_checkout"
    DELETE = "delete"
    LIST = "list"
    CURRENT = "current"


class MergeStrategy(str, Enum):
    """Strategy for merging branches (universes)."""

    THEIRS = "theirs"  # accept incoming branch entirely
    OURS = "ours"  # keep current branch entirely
    DEFAULT = "default"  # standard three-way merge


class BranchInfo(BaseModel):
    """Information about a Dolt branch (universe)."""

    name: str
    hash: str = ""
    latest_commit_message: str = ""
    latest_committer: str = ""
    latest_commit_date: datetime | None = None
    is_current: bool = False


class CommitInfo(BaseModel):
    """Information about a Dolt commit (game state snapshot)."""

    hash: str
    message: str
    author: str = ""
    timestamp: datetime | None = None
    parent_hash: str = ""


class DiffRow(BaseModel):
    """A single row change between two universe branches."""

    table: str
    diff_type: str  # "added", "removed", "modified"
    from_values: dict | None = None
    to_values: dict | None = None


class DiffResult(BaseModel):
    """Result of comparing two universe branches."""

    from_branch: str
    to_branch: str
    tables: list[str] = Field(default_factory=list)
    rows: list[DiffRow] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)  # table -> change count


class MergeResult(BaseModel):
    """Result of merging two universe branches."""

    success: bool
    source_branch: str
    target_branch: str
    commit_hash: str = ""
    conflicts: list[str] = Field(default_factory=list)
    message: str = ""


class QueryResult(BaseModel):
    """Result of a SQL query against a Dolt branch."""

    branch: str
    sql: str
    rows: list[dict]
    row_count: int
