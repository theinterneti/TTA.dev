#!/usr/bin/env python3
"""
Logseq Graph Agent (Sync Tool)

Automates the synchronization between the TTA codebase, documentation, and the Logseq Knowledge Base.

Features:
1. Coverage Sync: Updates Logseq pages with coverage data from component-maturity-analysis.json.
2. Namespace Management: Enforces TTA vs TTA.dev naming conventions.
3. Doc Processing: Maps new docs to Logseq pages and adds tags.
4. Code Processing: Adds Logseq citations to code files.
5. Block Sync: Extracts marked code blocks (# LogseqBlock: [[Page]]) and syncs them to Logseq.
6. Journal Sync: Aggregates project journals into TTA.notes.

Usage:
    python platform/kb-automation/src/tta_kb_automation/tools/logseq_graph_sync.py --sync-coverage
    python platform/kb-automation/src/tta_kb_automation/tools/logseq_graph_sync.py --process-files
    python platform/kb-automation/src/tta_kb_automation/tools/logseq_graph_sync.py --sync-journals
    python platform/kb-automation/src/tta_kb_automation/tools/logseq_graph_sync.py --all
"""

import argparse
import json
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

# Configuration
# Adjusted for location: platform/kb-automation/src/tta_kb_automation/tools/logseq_graph_sync.py
# parents[0] = tools
# parents[1] = tta_kb_automation
# parents[2] = src
# parents[3] = kb-automation
# parents[4] = platform
# parents[5] = TTA.dev (Root)
REPO_ROOT = Path(__file__).parents[5].resolve()
LOGSEQ_ROOT = Path(os.path.expanduser("~/repos/TTA-notes"))
PAGES_DIR = LOGSEQ_ROOT / "pages"
JOURNALS_DIR = LOGSEQ_ROOT / "journals"
MATURITY_FILE = REPO_ROOT / "component-maturity-analysis.json"

# Namespace Rules
NAMESPACE_RULES = {
    "TTA": [
        r"src/components/narrative_.*",
        r"src/components/game_.*",
        r"src/story/.*",
        r"recovered-tta-storytelling/.*",
    ],
    "TTA.dev": [
        r"src/components/neo4j_.*",
        r"src/components/docker_.*",
        r"src/components/monitoring_.*",
        r"scripts/.*",
        r"devops/.*",
        r"platform/.*",
        r"apps/.*",
        r"docs/.*",  # Top-level documentation
    ],
}

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    "node_modules",
    ".pytest_cache",
    "coverage",
    "htmlcov",
    ".vscode",
    ".idea",
    "dist",
    "build",
    ".mypy_cache",
    ".tox",
    ".env",
    "tmp",
    "temp",
    "site-packages",
    ".uv_cache",
    ".archive",
    "_archive",  # Archive directories (underscore variant)
    ".venv",
}

IGNORE_FILES = {
    ".DS_Store",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "component-maturity-analysis.json",
    "logseq_graph_agent.py",
    "logseq_graph_sync.py",
}

LANGUAGE_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".js": "javascript",
    ".md": "markdown",
    ".sh": "bash",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}

# Type inference for pages based on path patterns
PAGE_TYPE_RULES = [
    # Primitives
    (r".*/Primitives/.*", "[[Primitive]]"),
    (r".*Primitive$", "[[Primitive]]"),
    # Guides
    (r".*/Guides/.*", "[[Guide]]"),
    (r".*/How-To/.*", "[[How-To]]"),
    (r".*/Best Practices/.*", "[[Best Practices]]"),
    # Examples
    (r".*/Examples/.*", "[[Example]]"),
    # Packages
    (r".*/Packages/.*", "[[Package]]"),
    # Architecture
    (r".*/Architecture/.*", "[[Architecture]]"),
    # Integration
    (r".*/Integrations?/.*", "[[Integration]]"),
    # MCP
    (r".*/MCP/.*", "[[MCP]]"),
    # Patterns
    (r".*/Patterns/.*", "[[Pattern]]"),
    # Scripts - based on file type
    (r".*/Scripts/.*\.py$", "[[Script]]"),
    (r".*/Scripts/.*\.sh$", "[[Script]]"),
    # Tests
    (r".*/Tests?/.*", "[[Test]]"),
    # Config files
    (r".*\.(yaml|yml|json|toml)$", "[[Config]]"),
]


def infer_page_type(page_name: str, file_path: str = "") -> str:
    """Infer the type for a page based on its name and source file."""
    for pattern, page_type in PAGE_TYPE_RULES:
        if re.search(pattern, page_name, re.IGNORECASE):
            return page_type
        if file_path and re.search(pattern, file_path, re.IGNORECASE):
            return page_type

    # Default based on file extension
    if file_path:
        ext = Path(file_path).suffix
        if ext == ".py":
            return "[[Python]]"
        elif ext in [".ts", ".js"]:
            return "[[TypeScript]]"
        elif ext == ".md":
            return "[[Documentation]]"
        elif ext == ".sh":
            return "[[Script]]"

    return "[[File]]"


def setup_paths():
    """Verify and setup paths."""
    global PAGES_DIR, JOURNALS_DIR

    if (LOGSEQ_ROOT / "logseq" / "pages").exists():
        PAGES_DIR = LOGSEQ_ROOT / "logseq" / "pages"
        JOURNALS_DIR = LOGSEQ_ROOT / "logseq" / "journals"
    elif (LOGSEQ_ROOT / "pages").exists():
        PAGES_DIR = LOGSEQ_ROOT / "pages"
        JOURNALS_DIR = LOGSEQ_ROOT / "journals"
    else:
        print(f"⚠️ Warning: Could not find Logseq pages directory in {LOGSEQ_ROOT}")

    print(f"📂 Logseq Pages: {PAGES_DIR}")


def load_maturity_data() -> dict[str, Any]:
    """Load component maturity data."""
    if not MATURITY_FILE.exists():
        print(f"❌ Error: {MATURITY_FILE} not found.")
        return {}
    return json.loads(MATURITY_FILE.read_text())


def get_namespace(file_path: str) -> str:
    """Determine namespace for a file."""
    try:
        rel_path = os.path.relpath(file_path, REPO_ROOT)
    except ValueError:
        return "TTA.dev"

    for pattern in NAMESPACE_RULES["TTA"]:
        if re.match(pattern, rel_path):
            return "TTA"

    for pattern in NAMESPACE_RULES["TTA.dev"]:
        if re.match(pattern, rel_path):
            return "TTA.dev"

    return "TTA.dev"


def get_page_filename(page_name: str) -> str:
    """Convert page name to filename (Logseq convention)."""
    return page_name.replace("/", "___") + ".md"


def update_logseq_page(
    title: str,
    properties: dict[str, Any],
    body_append: str = "",
    body_replace: str = "",
):
    """Create or update a Logseq page."""
    filename = get_page_filename(title)
    file_path = PAGES_DIR / filename

    content = ""
    existing_props = {}
    existing_body = ""

    if file_path.exists():
        content = file_path.read_text()
        lines = content.splitlines()

        if lines and lines[0].startswith("title::"):
            for i, line in enumerate(lines):
                if "::" in line:
                    key, val = line.split("::", 1)
                    existing_props[key.strip()] = val.strip()
                else:
                    existing_body = "\n".join(lines[i:])
                    break
        else:
            existing_body = content
    else:
        print(f"✨ Creating new page: {title}")
        existing_props["title"] = title

    # Merge properties
    new_props = {**existing_props, **properties}

    # Reconstruct
    new_content = ""
    for k, v in new_props.items():
        new_content += f"{k}:: {v}\n"

    if body_replace:
        existing_body = "\n" + body_replace
    elif not existing_body.strip():
        existing_body = f"\n# {title}\nAuto-generated by Logseq Graph Agent."

    new_content += existing_body

    if body_append and body_append not in new_content:
        new_content += "\n" + body_append

    if not file_path.exists() or content != new_content:
        if not file_path.parent.exists():
            print(f"⚠️ Parent dir {file_path.parent} does not exist. Skipping write.")
            return

        file_path.write_text(new_content)
        print(f"✅ Updated {title}")


def sync_coverage(data: dict[str, Any]):
    """Sync coverage data to Logseq pages."""
    print("🔄 Syncing Coverage Data...")

    for group, components in data.items():
        for name, info in components.items():
            component_path = info.get("path", "")
            namespace = get_namespace(REPO_ROOT / component_path) if component_path else "TTA.dev"

            safe_name = name.replace(" ", "")
            page_name = f"{namespace}/Components/{safe_name}"

            coverage = info.get("coverage", {}).get("coverage", 0)
            status = info.get("current_stage", "Unknown")

            update_logseq_page(
                page_name,
                {
                    "coverage": f"{coverage}%",
                    "status": status,
                    "type": "Component",
                    "group": group,
                },
            )


def inject_citation(file_path: Path, page_name: str):
    """Inject Logseq citation into file."""
    try:
        content = file_path.read_text()
        citation = f"[[{page_name}]]"

        if citation in content:
            return

        print(f"💉 Injecting citation {citation} into {file_path.name}")

        ext = file_path.suffix
        if ext == ".py":
            lines = content.splitlines()
            insert_idx = 0
            if lines and lines[0].startswith("#!"):
                insert_idx = 1

            # Always insert as comment at insert_idx
            # This avoids issues with docstrings and ensures it's a valid comment
            lines.insert(insert_idx, f"# Logseq: {citation}  # noqa: E501, ERA001")

            file_path.write_text("\n".join(lines))

        elif ext in [".ts", ".js"]:
            lines = content.splitlines()
            lines.insert(0, f"// Logseq: {citation}")
            file_path.write_text("\n".join(lines))

        elif ext == ".md":
            file_path.write_text(content + f"\n\n---\n**Logseq:** {citation}")

    except Exception as e:
        print(f"❌ Failed to inject citation into {file_path}: {e}")


def extract_blocks(file_path: Path, content: str, namespace: str, rel_path: Path = None):
    """Extract and sync code blocks marked with # LogseqBlock: [[Page]]"""
    if rel_path is None:
        try:
            rel_path = file_path.relative_to(REPO_ROOT)
        except ValueError:
            # Fallback if file_path is already relative or absolute mismatch
            rel_path = file_path

    # Pattern: # LogseqBlock: [[PageName]] ... # EndBlock
    # Regex to find start
    block_pattern = r"#\s*LogseqBlock:\s*\[\[(.*?)\]\]"

    lines = content.splitlines()
    current_block_page = None
    current_block_content = []

    for line in lines:
        start_match = re.search(block_pattern, line)
        if start_match:
            if current_block_page:
                pass
            current_block_page = start_match.group(1)
            current_block_content = []
            continue

        if "# EndBlock" in line and current_block_page:
            # Sync block
            lang = LANGUAGE_MAP.get(file_path.suffix, "")
            raw_content = "\n".join(current_block_content)
            dedented_content = textwrap.dedent(raw_content)
            block_body = f"```{lang}\n{dedented_content}\n```"

            # Ensure page name has namespace if not provided
            if "/" not in current_block_page:
                current_block_page = f"{namespace}/Blocks/{current_block_page}"

            update_logseq_page(
                current_block_page,
                {"type": "CodeBlock", "source_file": str(rel_path), "language": lang},
                body_replace=block_body,
            )

            current_block_page = None
            continue

        if current_block_page:
            current_block_content.append(line)


def process_files(files=None):
    """Scan and process code/doc files."""
    print("🔍 Scanning files...")

    if files:
        file_iterator = [Path(f) for f in files]
    else:
        file_iterator = []
        for root, dirs, files_in_dir in os.walk(REPO_ROOT):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files_in_dir:
                file_iterator.append(Path(root) / file)

    for file_path in file_iterator:
        if file_path.name in IGNORE_FILES:
            continue

        if file_path.suffix not in LANGUAGE_MAP:
            continue

        namespace = get_namespace(str(file_path))
        try:
            rel_path = file_path.relative_to(REPO_ROOT)
        except ValueError:
            # If file is passed as absolute path or outside repo
            try:
                rel_path = file_path.resolve().relative_to(REPO_ROOT.resolve())
            except ValueError:
                continue

        # Page Name Logic
        parts = list(rel_path.parts)
        if parts[0] in ["src", "recovered-tta-storytelling", "platform", "apps"]:
            # Keep platform/apps as part of structure or remove?
            # In TTA.dev, platform/primitives/src/... is deep.
            # Let's keep the structure but capitalize.
            pass

        # Clean up parts
        cleaned_parts = []
        for p in parts:
            if p in [".", ".."]:
                continue
            cleaned_parts.append(p)
        parts = cleaned_parts

        parts = [p.capitalize() for p in parts]
        parts[-1] = Path(parts[-1]).stem
        page_name = f"{namespace}/{'/'.join(parts)}"

        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        except (FileNotFoundError, OSError):
            print(f"⚠️ Skipping broken file/link: {file_path}")
            continue

        # Infer page type from path patterns
        page_type = infer_page_type(page_name, str(rel_path))

        # Update File Page
        update_logseq_page(
            page_name,
            {
                "file_path": str(rel_path),
                "type": page_type,
                "language": LANGUAGE_MAP.get(file_path.suffix, "text"),
                "last_modified": mtime,
            },
        )

        # Inject Citation
        inject_citation(file_path, page_name)

        # Extract Blocks
        try:
            content = file_path.read_text()
            extract_blocks(file_path, content, namespace, rel_path=rel_path)
        except Exception:
            pass


def sync_journals():
    """Aggregate journals."""
    print("📓 Syncing Journals...")
    today = datetime.now().strftime("%Y_%m_%d")
    journal_file = JOURNALS_DIR / f"{today}.md"

    for root, _, files in os.walk(REPO_ROOT):
        if "JOURNAL.md" in files:
            j_path = Path(root) / "JOURNAL.md"
            content = j_path.read_text()
            if not content.strip():
                continue

            print(f"Found journal entry in {j_path}")
            entry = f"\n### Update from {j_path.parent.name}\n{content}\n"

            if journal_file.exists():
                current_content = journal_file.read_text()
                if entry.strip() not in current_content:
                    journal_file.write_text(current_content + "\n" + entry)
            else:
                journal_file.write_text(entry)


def annotate_existing_pages(dry_run: bool = True):
    """Add type annotations to existing pages that are missing them."""
    print("📝 Annotating existing pages...")

    if not PAGES_DIR.exists():
        print(f"❌ Pages directory not found: {PAGES_DIR}")
        return

    pages = list(PAGES_DIR.glob("*.md"))
    print(f"📄 Found {len(pages)} pages")

    updated = 0
    for page_path in pages:
        try:
            content = page_path.read_text()
            lines = content.splitlines()

            # Parse existing properties
            properties = {}
            body_start = 0
            for i, line in enumerate(lines):
                if "::" in line and not line.strip().startswith("#"):
                    key, val = line.split("::", 1)
                    key = key.strip()
                    if key.replace("-", "_").replace("_", "").isalnum():
                        properties[key] = val.strip()
                        body_start = i + 1
                    else:
                        break
                elif line.strip() and not line.strip().startswith("#"):
                    break
                elif line.strip().startswith("#"):
                    body_start = i
                    break

            # Skip if already has type
            if "type" in properties:
                continue

            # Infer type from page name
            page_name = page_path.stem.replace("___", "/")
            page_type = infer_page_type(page_name)

            if dry_run:
                print(f"   Would add type:: {page_type} to {page_path.name}")
            else:
                # Add type property
                properties["type"] = page_type

                # Rebuild content
                new_lines = []
                prop_order = ["title", "alias", "type", "category", "status", "tags"]
                written = set()

                for prop in prop_order:
                    if prop in properties:
                        new_lines.append(f"{prop}:: {properties[prop]}")
                        written.add(prop)

                for key, val in properties.items():
                    if key not in written:
                        new_lines.append(f"{key}:: {val}")

                body = "\n".join(lines[body_start:]).strip()
                if body:
                    new_lines.append("")
                    new_lines.append(body)

                page_path.write_text("\n".join(new_lines) + "\n")
                print(f"   ✅ Added type:: {page_type} to {page_path.name}")

            updated += 1

        except Exception as e:
            print(f"   ⚠️ Error processing {page_path.name}: {e}")

    if dry_run:
        print(f"\n💡 Would update {updated} pages. Run without --dry-run to apply.")
    else:
        print(f"\n✅ Updated {updated} pages")


def main():
    parser = argparse.ArgumentParser(description="Logseq Graph Agent")
    parser.add_argument("--sync-coverage", action="store_true", help="Sync coverage data")
    parser.add_argument("--process-files", action="store_true", help="Process code/doc files")
    parser.add_argument("--sync-journals", action="store_true", help="Sync journals")
    parser.add_argument(
        "--annotate-types", action="store_true", help="Add type annotations to existing pages"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying (for --annotate-types)",
    )
    parser.add_argument("--all", action="store_true", help="Run all tasks")
    parser.add_argument("files", nargs="*", help="Specific files to process")

    args = parser.parse_args()
    setup_paths()

    if args.sync_coverage or args.all:
        data = load_maturity_data()
        sync_coverage(data)

    if args.process_files or args.all or args.files:
        process_files(args.files)

    if args.sync_journals or args.all:
        sync_journals()

    if args.annotate_types:
        annotate_existing_pages(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
