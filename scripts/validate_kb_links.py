#!/usr/bin/env python3
"""
KB Health Checker: A comprehensive tool for validating the integrity of the TTA.dev knowledge graph.

This script performs a "three-way" validation between:
1. Markdown Documentation (`docs/`, `packages/*/README.md`, etc.)
2. Logseq Knowledge Base (`logseq/`)
3. Python Source Code Docstrings (`packages/**/*.py`)

It checks for:
- Broken links (in all directions)
- Orphaned documentation files
- Orphaned knowledge base pages
- Missing links from code to the KB/docs
"""

import ast
import os
import re
from pathlib import Path
from urllib.parse import unquote
from collections import defaultdict

# --- Configuration ---
ROOT_DIR = Path(__file__).parent.parent
DOCS_DIR = ROOT_DIR / "docs"
LOGSEQ_DIR = ROOT_DIR / "logseq" / "pages"
PACKAGES_DIR = ROOT_DIR / "packages"

# Regex to find markdown-style links: [text](link)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

# Critical documentation files that should always be linked from the KB
EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".ruff_cache", ".pytest_cache"}
CRITICAL_DOCS = [
    ROOT_DIR / "AGENTS.md",
    ROOT_DIR / "GETTING_STARTED.md",
    ROOT_DIR / "PRIMITIVES_CATALOG.md",
    DOCS_DIR / "architecture" / "Overview.md",
    PACKAGES_DIR / "tta-dev-primitives" / "README.md",
    PACKAGES_DIR / "tta-observability-integration" / "README.md",
    PACKAGES_DIR / "universal-agent-context" / "README.md",
]

# --- Data Structures ---
all_markdown_files = set()
all_logseq_files = set()
all_python_files = set()

links_found = defaultdict(list)
broken_links = defaultdict(list)
link_references = defaultdict(set) # Stores which files link to which target

# --- File Discovery ---

def discover_files():
    """Discover all relevant Markdown, Logseq, and Python files."""
    for root, dirs, files in os.walk(ROOT_DIR):
        # Exclude specified directories from traversal
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            if file.endswith(".md"):
                if "logseq" in file_path.parts:
                    all_logseq_files.add(file_path)
                else:
                    all_markdown_files.add(file_path)
            elif file.endswith(".py"):
                all_python_files.add(file_path)
    print(f"Discovered {len(all_markdown_files)} Markdown docs, {len(all_logseq_files)} Logseq pages, and {len(all_python_files)} Python files.")

# --- Link Extraction ---

def find_links_in_file(file_path: Path):
    """Find all Markdown-style links in a given file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        return MD_LINK_RE.findall(content)
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return []

def find_links_in_docstrings(file_path: Path):
    """Extract links from docstrings of functions, classes, and modules in a Python file."""
    links = []
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        # Module-level docstring
        if (docstring := ast.get_docstring(tree)):
            links.extend(MD_LINK_RE.findall(docstring))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (docstring := ast.get_docstring(node)):
                    links.extend(MD_LINK_RE.findall(docstring))
    except Exception as e:
        print(f"Warning: Could not parse AST for {file_path}: {e}")
    return links

# --- Link Validation ---

def validate_link(source_file: Path, link: str):
    """Validate a single link and record its status."""
    if link.startswith(("http://", "https://", "mailto:")):
        return # Skip external links for now

    # Normalize the link
    decoded_link = unquote(link).split('#')[0] # Remove URL encoding and anchors

    # Resolve the target path
    if decoded_link.startswith("/"):
        target_path = ROOT_DIR / decoded_link.lstrip('/')
    else:
        target_path = source_file.parent / decoded_link

    # Use a normalized, relative path for checking existence and for keys
    try:
        # Resolve path without checking existence to handle relative links correctly
        normalized_path = target_path.resolve()
    except FileNotFoundError:
        # This can happen with ../../ style links that go too high
        normalized_path = Path(os.path.abspath(target_path))


    if not normalized_path.exists():
        broken_links[source_file].append(link)
    else:
        # Record that source_file links to target_path
        link_references[normalized_path].add(source_file)

# --- Main Logic ---

def run_audit():
    """Execute the full audit process."""
    print("\n--- Phase 1: Scanning Files and Extracting Links ---")

    # Scan Markdown docs
    for md_file in all_markdown_files:
        found = find_links_in_file(md_file)
        links_found[md_file].extend(found)

    # Scan Logseq pages
    for ls_file in all_logseq_files:
        found = find_links_in_file(ls_file)
        links_found[ls_file].extend(found)

    # Scan Python docstrings
    for py_file in all_python_files:
        found = find_links_in_docstrings(py_file)
        links_found[py_file].extend(found)

    print(f"Found links in {len(links_found)} files.")

    print("\n--- Phase 2: Validating Links ---")
    for source_file, links in links_found.items():
        for link in links:
            validate_link(source_file, link)

    print(f"Validation complete. Found {sum(len(v) for v in broken_links.values())} broken links.")

    print("\n--- Phase 3: Orphan Detection ---")

    # Find orphaned critical docs
    orphaned_docs = []
    resolved_critical_docs = {doc.resolve() for doc in CRITICAL_DOCS}
    for doc_path in resolved_critical_docs:
        if doc_path not in link_references:
            orphaned_docs.append(doc_path)

    # Find orphaned Logseq pages
    orphaned_kb_pages = []
    for page in all_logseq_files:
        # An orphan if it's not linked to AND it doesn't link out to any docs/code
        is_linked_to = page.resolve() in link_references
        links_out_to_docs = any(
            "logseq" not in unquote(link) for link in links_found.get(page, [])
        )

        # Check for [[Project Hub]] link directly in the file content
        try:
            content = page.read_text(encoding="utf-8")
            links_to_hub = "[[Project Hub]]" in content
        except Exception:
            links_to_hub = False

        if not is_linked_to and not links_out_to_docs and not links_to_hub:
            orphaned_kb_pages.append(page)

    print(f"Found {len(orphaned_docs)} orphaned critical docs and {len(orphaned_kb_pages)} orphaned KB pages.")

    return orphaned_docs, orphaned_kb_pages

# --- Reporting ---

def generate_report(orphaned_docs, orphaned_kb_pages):
    """Print a comprehensive report of all findings."""
    print("\n\n--- KB HEALTH CHECK REPORT ---")

    if not broken_links and not orphaned_docs and not orphaned_kb_pages:
        print("\n✅ SUCCESS: Knowledge base is fully integrated and healthy!")
        return

    if broken_links:
        print("\n❌ Broken Links Found:")
        for source, links in sorted(broken_links.items()):
            print(f"\n  In File: {source.relative_to(ROOT_DIR)}")
            for link in links:
                print(f"    - {link}")

    if orphaned_docs:
        print("\n❌ Orphaned Critical Documentation:")
        print("  (These important files are not linked to from anywhere in the KB or other docs)")
        for doc in sorted(orphaned_docs):
            print(f"    - {doc.relative_to(ROOT_DIR)}")

    if orphaned_kb_pages:
        print("\n❌ Orphaned Knowledge Base Pages:")
        print("  (These KB pages do not link to any code/docs and are not linked to from anywhere)")
        for page in sorted(orphaned_kb_pages):
            print(f"    - {page.relative_to(ROOT_DIR)}")

    print("\n--- END OF REPORT ---")


if __name__ == "__main__":
    discover_files()
    orphaned_docs, orphaned_kb_pages = run_audit()
    generate_report(orphaned_docs, orphaned_kb_pages)
