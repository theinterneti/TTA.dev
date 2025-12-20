#!/usr/bin/env python3
"""Generate KB pages from primitive class docstrings.

This script scans the tta_dev_primitives package and generates
Logseq-compatible KB pages for each primitive class.

Usage:
    python scripts/generate_kb_pages.py [--dry-run] [--verbose]
"""

import argparse
import ast
import re
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
TTA_DEV_ROOT = SCRIPT_DIR.parent
PRIMITIVES_SRC = TTA_DEV_ROOT / "platform/primitives/src/tta_dev_primitives"
PAGES_DIR = TTA_DEV_ROOT / "pages"

# Categories to scan
CATEGORIES = [
    ("core", "Core"),
    ("recovery", "Recovery"),
    ("adaptive", "Adaptive"),
    ("performance", "Performance"),
    ("testing", "Testing"),
    ("observability", "Observability"),
    ("knowledge", "Knowledge"),
    ("orchestration", "Orchestration"),
]


def extract_classes_from_file(filepath: Path) -> list[dict]:
    """Extract class names and docstrings from a Python file."""
    classes = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "Primitive" in node.name or node.name in [
                    "RetryStrategy",
                    "CircuitBreaker",
                ]:
                    docstring = ast.get_docstring(node) or ""
                    classes.append(
                        {
                            "name": node.name,
                            "docstring": docstring,
                            "file": str(filepath.relative_to(TTA_DEV_ROOT)),
                        }
                    )
    except Exception as e:
        print(f"  [error] Failed to parse {filepath}: {e}")
    return classes


def generate_kb_page(cls: dict, category: str) -> str:
    """Generate KB page content for a primitive class."""
    name = cls["name"]
    docstring = cls["docstring"]
    source_file = cls["file"]

    # Extract examples (may have multiple)
    examples = re.findall(
        r"(?:Example|Usage)s?:\s*```python\s*(.*?)```", docstring, re.DOTALL | re.IGNORECASE
    )

    # Extract Args section
    args_match = re.search(r"Args:\s*(.*?)(?:Returns:|Raises:|Example|$)", docstring, re.DOTALL)
    args_section = args_match.group(1).strip() if args_match else ""

    # Extract Returns section
    returns_match = re.search(r"Returns:\s*(.*?)(?:Raises:|Example|Args:|$)", docstring, re.DOTALL)
    returns_section = returns_match.group(1).strip() if returns_match else ""

    # Clean docstring for description (first paragraph only)
    description = docstring.split("\n\n")[0].strip() if docstring else ""
    # Remove any leftover section headers
    description = re.sub(r"(Args|Returns|Raises|Example)s?:.*", "", description, flags=re.DOTALL).strip()

    # Generate page content
    lines = [
        f"type:: primitive",
        f"category:: {category}",
        f"status:: documented",
        f"generated:: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"# {name}",
        "",
        f"**Source:** `{source_file}`",
        "",
        "## Overview",
        "",
        description if description else f"*{name} primitive - documentation pending.*",
        "",
    ]

    # Add parameters section if available
    if args_section:
        lines.extend([
            "## Parameters",
            "",
        ])
        for line in args_section.split("\n"):
            if line.strip():
                lines.append(f"- {line.strip()}")
        lines.append("")

    # Add returns section if available
    if returns_section:
        lines.extend([
            "## Returns",
            "",
            returns_section,
            "",
        ])

    # Add examples
    if examples:
        lines.extend([
            "## Usage Examples",
            "",
        ])
        for i, example in enumerate(examples):
            if len(examples) > 1:
                lines.append(f"### Example {i + 1}")
                lines.append("")
            lines.extend([
                "```python",
                example.strip(),
                "```",
                "",
            ])

    # Add gotchas/tips section for key primitives
    gotchas = get_gotchas(name)
    if gotchas:
        lines.extend([
            "## Tips & Gotchas",
            "",
        ])
        lines.extend(gotchas)
        lines.append("")

    lines.extend([
        "## Related",
        "",
        f"- [[TTA.dev/Primitives]] - Primitives index",
        f"- [[TTA.dev/Primitives/{category}]] - {category} primitives",
        "",
    ])

    return "\n".join(lines)


def get_gotchas(name: str) -> list[str]:
    """Return tips and gotchas for specific primitives."""
    gotchas = {
        "RetryPrimitive": [
            "- ⚠️ Set appropriate `max_retries` to avoid infinite loops",
            "- 💡 Use `jitter=True` to prevent thundering herd",
            "- 📝 Only retries on transient errors by default",
        ],
        "CircuitBreaker": [
            "- ⚠️ Circuit stays open for `reset_timeout` seconds",
            "- 💡 Monitor circuit state via metrics",
            "- 📝 Half-open state allows one test request",
        ],
        "TimeoutPrimitive": [
            "- ⚠️ Cancelled tasks may leave side effects",
            "- 💡 Combine with RetryPrimitive for resilience",
            "- 📝 Use shorter timeouts for user-facing operations",
        ],
        "CachePrimitive": [
            "- ⚠️ Cache invalidation is hard - set appropriate TTL",
            "- 💡 Use with MemoryPrimitive for bounded caching",
            "- 📝 Consider cache key uniqueness carefully",
        ],
        "ParallelPrimitive": [
            "- ⚠️ Errors in one branch don't cancel others by default",
            "- 💡 Set `max_concurrency` to limit resource usage",
            "- 📝 Results maintain order of input primitives",
        ],
    }
    return gotchas.get(name, [])


def main():
    parser = argparse.ArgumentParser(description="Generate KB pages from primitives")
    parser.add_argument("--dry-run", action="store_true", help="Show without writing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("=" * 60)
    print("TTA.dev KB Page Generator")
    print("=" * 60)

    if args.dry_run:
        print("🔍 DRY RUN - No files will be written\n")

    total_generated = 0

    for category_dir, category_name in CATEGORIES:
        category_path = PRIMITIVES_SRC / category_dir
        if not category_path.exists():
            continue

        print(f"\n📂 Scanning {category_name} ({category_dir}/)")

        for py_file in category_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            classes = extract_classes_from_file(py_file)
            for cls in classes:
                page_name = f"TTA.dev___Primitives___{cls['name']}.md"
                page_path = PAGES_DIR / page_name
                content = generate_kb_page(cls, category_name)

                if args.verbose:
                    print(f"  [generate] {cls['name']} -> {page_name}")

                if not args.dry_run:
                    page_path.write_text(content, encoding="utf-8")

                total_generated += 1

    print(f"\n✅ Generated {total_generated} KB pages")
    print("=" * 60)


if __name__ == "__main__":
    main()
