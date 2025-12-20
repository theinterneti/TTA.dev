#!/usr/bin/env python3
"""Journal Synchronization Script for TTA.dev Multi-Agent Worktrees.

Syncs journal entries from worktree-specific logseq/journals/ directories
to the canonical shared journals location.

# See: [[TTA.dev/Journal Sync]]

Usage:
    python scripts/sync_journals.py [--dry-run] [--verbose]
    python scripts/sync_journals.py --sync-to-notes  # Also sync to TTA-notes

Source Directories:
    - /home/thein/repos/TTA.dev/logseq/journals/ (agent: main)
    - /home/thein/repos/TTA.dev-augment/logseq/journals/ (agent: augment)
    - /home/thein/repos/TTA.dev-cline/logseq/journals/ (agent: cline)
    - /home/thein/repos/TTA.dev-copilot/logseq/journals/ (agent: copilot)

Primary Destination:
    - /home/thein/repos/TTA.dev/journals/

Secondary Destination (with --sync-to-notes):
    - /home/thein/repos/TTA-notes/journals/
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class JournalEntry(NamedTuple):
    """Represents a journal entry with metadata."""

    source_path: Path
    agent: str
    date: str  # YYYY-MM-DD format
    content: str
    content_hash: str


# Configuration
REPO_ROOT = Path("/home/thein/repos")
TTA_DEV_ROOT = REPO_ROOT / "TTA.dev"
TTA_NOTES_ROOT = REPO_ROOT / "TTA-notes"

# Source directories mapping: path -> agent name
WORKTREE_JOURNALS = {
    TTA_DEV_ROOT / "logseq" / "journals": "main",
    REPO_ROOT / "TTA.dev-augment" / "logseq" / "journals": "augment",
    REPO_ROOT / "TTA.dev-cline" / "logseq" / "journals": "cline",
    REPO_ROOT / "TTA.dev-copilot" / "logseq" / "journals": "copilot",
}

# Destination directories
PRIMARY_DEST = TTA_DEV_ROOT / "journals"
SECONDARY_DEST = TTA_NOTES_ROOT / "journals"

# Date format patterns
DATE_PATTERN_UNDERSCORE = re.compile(r"^(\d{4})_(\d{2})_(\d{2})\.md$")
DATE_PATTERN_DASH = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:_(\w+))?\.md$")


def normalize_date_filename(filename: str) -> str | None:
    """Convert date filename to YYYY-MM-DD format. Returns None if not a date file."""
    # Try underscore format: 2025_11_20.md
    match = DATE_PATTERN_UNDERSCORE.match(filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # Try dash format: 2025-11-20.md or 2025-11-20_agent.md
    match = DATE_PATTERN_DASH.match(filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    return None


def compute_content_hash(content: str) -> str:
    """Compute a hash of the content for change detection (not for security).

    Excludes the 'synced::' line from hash computation to avoid false updates.
    """
    # Remove synced:: line before hashing to avoid timestamp-based differences
    lines = [line for line in content.split("\n") if not line.startswith("synced::")]
    normalized = "\n".join(lines)
    return hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()[:12]


def add_agent_frontmatter(content: str, agent: str, date: str) -> str:
    """Add or update agent frontmatter in journal content.

    Only updates synced:: timestamp if content actually changed.
    """
    lines = content.split("\n")

    # Check if frontmatter already exists (starts with agent::)
    if lines and lines[0].startswith("agent::"):
        # Already has frontmatter, update synced timestamp only
        new_lines = []
        for line in lines:
            if line.startswith("synced::"):
                new_lines.append(f"synced:: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    # Check for other frontmatter patterns
    frontmatter_added = False
    new_lines = []

    for i, line in enumerate(lines):
        if i == 0 and line.startswith("#"):
            # Has a title, add frontmatter before it
            new_lines.append(f"agent:: {agent}")
            new_lines.append(f"date:: [[{date}]]")
            new_lines.append(f"synced:: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            new_lines.append("")
            frontmatter_added = True
        new_lines.append(line)

    if not frontmatter_added:
        # No title found, prepend frontmatter
        header = [
            f"# {date}",
            "",
            f"agent:: {agent}",
            f"date:: [[{date}]]",
            f"synced:: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
        ]
        return "\n".join(header + lines)

    return "\n".join(new_lines)


def scan_journal_sources(verbose: bool = False) -> dict[str, list[JournalEntry]]:
    """Scan all worktree journal directories and collect entries by date."""
    entries_by_date: dict[str, list[JournalEntry]] = {}

    for journal_dir, agent in WORKTREE_JOURNALS.items():
        if not journal_dir.exists():
            if verbose:
                print(f"  [skip] {journal_dir} does not exist")
            continue

        for file_path in journal_dir.glob("*.md"):
            date = normalize_date_filename(file_path.name)
            if not date:
                if verbose:
                    print(f"  [skip] {file_path.name} - not a date format")
                continue

            content = file_path.read_text(encoding="utf-8")
            content_hash = compute_content_hash(content)

            entry = JournalEntry(
                source_path=file_path,
                agent=agent,
                date=date,
                content=content,
                content_hash=content_hash,
            )

            if date not in entries_by_date:
                entries_by_date[date] = []
            entries_by_date[date].append(entry)

            if verbose:
                print(f"  [found] {date} from {agent}: {file_path.name}")

    return entries_by_date


def get_existing_entries(dest_dir: Path) -> dict[str, set[str]]:
    """Get existing entries in destination directory. Returns {date: {agents}}."""
    existing: dict[str, set[str]] = {}

    if not dest_dir.exists():
        return existing

    for file_path in dest_dir.glob("*.md"):
        match = DATE_PATTERN_DASH.match(file_path.name)
        if match:
            date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            agent = match.group(4) if match.group(4) else "unknown"

            if date not in existing:
                existing[date] = set()
            existing[date].add(agent)

    return existing


def sync_to_destination(
    entries_by_date: dict[str, list[JournalEntry]],
    dest_dir: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """Sync journal entries to destination directory.

    Returns: (created, updated, skipped) counts
    """
    created = 0
    updated = 0
    skipped = 0

    dest_dir.mkdir(parents=True, exist_ok=True)

    for date, entries in sorted(entries_by_date.items()):
        if len(entries) == 1:
            # Single agent for this date - use standard format
            entry = entries[0]
            dest_file = dest_dir / f"{date}.md"
            content = add_agent_frontmatter(entry.content, entry.agent, date)

            if dest_file.exists():
                existing_content = dest_file.read_text(encoding="utf-8")
                existing_hash = compute_content_hash(existing_content)
                new_hash = compute_content_hash(content)

                if existing_hash == new_hash:
                    skipped += 1
                    if verbose:
                        print(f"  [skip] {dest_file.name} - unchanged")
                    continue

                if not dry_run:
                    dest_file.write_text(content, encoding="utf-8")
                updated += 1
                if verbose:
                    print(f"  [update] {dest_file.name}")
            else:
                if not dry_run:
                    dest_file.write_text(content, encoding="utf-8")
                created += 1
                if verbose:
                    print(f"  [create] {dest_file.name}")
        else:
            # Multiple agents for this date - use agent suffix
            for entry in entries:
                dest_file = dest_dir / f"{date}_{entry.agent}.md"
                content = add_agent_frontmatter(entry.content, entry.agent, date)

                if dest_file.exists():
                    existing_content = dest_file.read_text(encoding="utf-8")
                    existing_hash = compute_content_hash(existing_content)
                    new_hash = compute_content_hash(content)

                    if existing_hash == new_hash:
                        skipped += 1
                        if verbose:
                            print(f"  [skip] {dest_file.name} - unchanged")
                        continue

                    if not dry_run:
                        dest_file.write_text(content, encoding="utf-8")
                    updated += 1
                    if verbose:
                        print(f"  [update] {dest_file.name}")
                else:
                    if not dry_run:
                        dest_file.write_text(content, encoding="utf-8")
                    created += 1
                    if verbose:
                        print(f"  [create] {dest_file.name}")

    return created, updated, skipped


def sync_primary_to_notes(
    dry_run: bool = False,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """Sync any files in PRIMARY_DEST to SECONDARY_DEST that aren't from logseq sources.

    This handles files created directly in TTA.dev/journals/ (like manual entries).
    """
    created = 0
    updated = 0
    skipped = 0

    SECONDARY_DEST.mkdir(parents=True, exist_ok=True)

    for src_file in PRIMARY_DEST.glob("*.md"):
        dest_file = SECONDARY_DEST / src_file.name

        src_content = src_file.read_text(encoding="utf-8")
        src_hash = compute_content_hash(src_content)

        if dest_file.exists():
            dest_content = dest_file.read_text(encoding="utf-8")
            dest_hash = compute_content_hash(dest_content)

            if src_hash == dest_hash:
                skipped += 1
                if verbose:
                    print(f"  [skip] {src_file.name} - unchanged")
                continue

            if not dry_run:
                shutil.copy2(src_file, dest_file)
            updated += 1
            if verbose:
                print(f"  [update] {src_file.name}")
        else:
            if not dry_run:
                shutil.copy2(src_file, dest_file)
            created += 1
            if verbose:
                print(f"  [create] {src_file.name}")

    return created, updated, skipped


def main():
    """Main entry point for journal sync."""
    parser = argparse.ArgumentParser(
        description="Sync journals from worktree logseq/journals/ to shared locations"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--sync-to-notes",
        action="store_true",
        help="Also sync to TTA-notes repository",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("TTA.dev Journal Synchronization")
    print("=" * 60)

    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made\n")

    # Step 1: Scan all logseq sources
    print("\n📂 Scanning journal sources...")
    entries = scan_journal_sources(verbose=args.verbose)
    total_entries = sum(len(e) for e in entries.values())
    print(f"   Found {total_entries} entries across {len(entries)} dates")

    # Step 2: Sync to primary destination (from logseq sources)
    print(f"\n📥 Syncing to primary: {PRIMARY_DEST}")
    c1, u1, s1 = sync_to_destination(
        entries, PRIMARY_DEST, dry_run=args.dry_run, verbose=args.verbose
    )
    print(f"   Created: {c1}, Updated: {u1}, Skipped: {s1}")

    # Step 3: Optionally sync to TTA-notes
    if args.sync_to_notes:
        # First sync logseq sources to TTA-notes
        print(f"\n📥 Syncing logseq sources to TTA-notes: {SECONDARY_DEST}")
        c2, u2, s2 = sync_to_destination(
            entries, SECONDARY_DEST, dry_run=args.dry_run, verbose=args.verbose
        )
        print(f"   Created: {c2}, Updated: {u2}, Skipped: {s2}")

        # Then sync any files in primary that aren't in TTA-notes yet
        print(f"\n📥 Syncing primary to TTA-notes (catch-up):")
        c3, u3, s3 = sync_primary_to_notes(
            dry_run=args.dry_run, verbose=args.verbose
        )
        print(f"   Created: {c3}, Updated: {u3}, Skipped: {s3}")

    print("\n" + "=" * 60)
    print("✅ Journal sync complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
