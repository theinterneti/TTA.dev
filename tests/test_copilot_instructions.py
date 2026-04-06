"""Tests for Copilot instruction files.

Validates that instruction files have correct structure, glob patterns
match real files, and guidance is consistent across all files.
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTRUCTIONS_DIR = REPO_ROOT / ".github" / "instructions"
COPILOT_INSTRUCTIONS = REPO_ROOT / ".github" / "copilot-instructions.md"

# Expected instruction files and their glob patterns
EXPECTED_FILES = {
    "python.instructions.md": "ttadev/**/*.py",
    "testing.instructions.md": "**/tests/**/*.py,**/*_test.py,**/test_*.py",
    "scripts.instructions.md": "scripts/**/*.py",
    "documentation.instructions.md": "**/*.md,**/README.md,**/CHANGELOG.md",
}


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    assert match, f"No YAML frontmatter found in {path.name}"
    return yaml.safe_load(match.group(1))


def _glob_matches(pattern: str) -> list[Path]:
    """Return files matching a glob pattern relative to repo root."""
    return list(REPO_ROOT.glob(pattern))


# --- File existence and structure ---


def test_copilot_instructions_exists():
    """Main copilot-instructions.md must exist."""
    assert COPILOT_INSTRUCTIONS.is_file(), "Missing .github/copilot-instructions.md"


def test_copilot_instructions_has_key_sections():
    """Main copilot-instructions.md has required sections."""
    content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    required = [
        "Package Manager",
        "Python Standards",
        "Testing",
        "Code Style",
        "Workflow Primitives",
    ]
    for section in required:
        assert section in content, f"Missing section '{section}' in copilot-instructions.md"


def test_all_expected_instruction_files_exist():
    """Every expected instruction file must be present."""
    for filename in EXPECTED_FILES:
        path = INSTRUCTIONS_DIR / filename
        assert path.is_file(), f"Missing instruction file: {filename}"


def test_instruction_files_have_valid_frontmatter():
    """Each instruction file must have YAML frontmatter with applyTo and description."""
    for filename in EXPECTED_FILES:
        path = INSTRUCTIONS_DIR / filename
        fm = _parse_frontmatter(path)
        assert "applyTo" in fm, f"{filename}: missing 'applyTo' in frontmatter"
        assert "description" in fm, f"{filename}: missing 'description' in frontmatter"
        assert isinstance(fm["applyTo"], str), f"{filename}: 'applyTo' must be a string"
        assert len(fm["description"]) > 0, f"{filename}: 'description' must not be empty"


def test_instruction_files_have_markdown_headers():
    """Each instruction file should have at least one markdown header."""
    for filename in EXPECTED_FILES:
        path = INSTRUCTIONS_DIR / filename
        content = path.read_text(encoding="utf-8")
        headers = re.findall(r"^#+\s+.+$", content, re.MULTILINE)
        assert len(headers) >= 1, f"{filename}: no markdown headers found"


# --- Glob pattern validation ---


def test_glob_patterns_match_expected():
    """Each instruction file's applyTo must match the expected pattern."""
    for filename, expected_pattern in EXPECTED_FILES.items():
        path = INSTRUCTIONS_DIR / filename
        fm = _parse_frontmatter(path)
        assert fm["applyTo"] == expected_pattern, (
            f"{filename}: applyTo is '{fm['applyTo']}', expected '{expected_pattern}'"
        )


def test_glob_patterns_match_real_files():
    """Every glob pattern must match at least one real file in the repo."""
    for filename, pattern_str in EXPECTED_FILES.items():
        patterns = [p.strip() for p in pattern_str.split(",")]
        total_matches = 0
        for pattern in patterns:
            matches = _glob_matches(pattern)
            total_matches += len(matches)
        assert total_matches > 0, (
            f"{filename}: pattern '{pattern_str}' matches no files in the repo"
        )


def test_python_pattern_matches_ttadev_source():
    """Python instructions should match the current ttadev Python package layout."""
    matches = _glob_matches("ttadev/**/*.py")
    assert len(matches) > 0, "No ttadev Python files found"
    for m in matches:
        rel = m.relative_to(REPO_ROOT)
        assert rel.parts[0] == "ttadev", f"Unexpected match: {rel}"


def test_testing_pattern_matches_test_files():
    """Testing instructions should match test files."""
    patterns = ["**/tests/**/*.py", "**/*_test.py", "**/test_*.py"]
    all_matches = set()
    for pattern in patterns:
        all_matches.update(_glob_matches(pattern))
    assert len(all_matches) > 0, "No test files found"


def test_scripts_pattern_matches_scripts_dir():
    """Scripts instructions should match files under scripts/."""
    matches = _glob_matches("scripts/**/*.py")
    assert len(matches) > 0, "No script files found"
    for m in matches:
        rel = m.relative_to(REPO_ROOT)
        assert rel.parts[0] == "scripts", f"Unexpected match: {rel}"


def test_logseq_pattern_matches_logseq_dir():
    """Logseq instructions should match files under logseq/."""
    matches = _glob_matches("logseq/**/*.md")
    assert len(matches) > 0, "No logseq markdown files found"
    for m in matches:
        rel = m.relative_to(REPO_ROOT)
        assert rel.parts[0] == "logseq", f"Unexpected match: {rel}"


def test_documentation_pattern_matches_markdown_files():
    """Documentation instructions should match markdown files across the repo."""
    matches = _glob_matches("**/*.md")
    assert len(matches) > 0, "No markdown files found"


# --- Overlap detection ---


def test_no_exact_pattern_duplicates():
    """No two instruction files should have identical applyTo patterns."""
    seen: dict[str, str] = {}
    for filename in EXPECTED_FILES:
        path = INSTRUCTIONS_DIR / filename
        fm = _parse_frontmatter(path)
        pattern = fm["applyTo"]
        if pattern in seen:
            raise AssertionError(f"Duplicate applyTo '{pattern}' in {filename} and {seen[pattern]}")
        seen[pattern] = filename


def test_documentation_and_logseq_overlap_acknowledged():
    """Logseq markdown files are a subset of the documentation glob.

    This is expected behavior — Copilot applies the more specific
    logseq instruction when editing logseq files. This test documents
    and verifies the overlap.
    """
    doc_pattern = "**/*.md"
    logseq_pattern = "logseq/**/*.md"

    logseq_matches = set(_glob_matches(logseq_pattern))
    doc_matches = set(_glob_matches(doc_pattern))

    overlap = logseq_matches & doc_matches
    assert len(overlap) > 0, (
        "Expected overlap between documentation and logseq patterns — "
        "logseq files should match both"
    )
    # All logseq matches should be a subset of documentation matches
    assert logseq_matches <= doc_matches, "Logseq files should be a subset of all markdown files"


# --- Content consistency checks ---


def test_consistent_package_manager_guidance():
    """All files referencing package commands should use 'uv'."""
    main_content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    assert "uv" in main_content, "Main instructions should mention 'uv'"
    assert "never `pip`" in main_content.lower() or "never pip" in main_content.lower(), (
        "Main instructions should warn against pip"
    )

    # Files with shell command examples should all use 'uv' commands
    for filename in ["python.instructions.md", "scripts.instructions.md"]:
        content = (INSTRUCTIONS_DIR / filename).read_text(encoding="utf-8")
        assert "uv run" in content, f"{filename} should use 'uv run' in commands"


def test_consistent_testing_framework():
    """Both main and testing instructions should reference pytest and MockPrimitive."""
    main_content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    testing_content = (INSTRUCTIONS_DIR / "testing.instructions.md").read_text(encoding="utf-8")

    for content, name in [
        (main_content, "copilot-instructions"),
        (testing_content, "testing"),
    ]:
        assert "pytest" in content, f"{name} should reference pytest"
        assert "MockPrimitive" in content, f"{name} should reference MockPrimitive"


def test_consistent_primitives_over_manual_loops():
    """Python, scripts, and main instructions should all prefer primitives over manual loops."""
    files_to_check = [
        COPILOT_INSTRUCTIONS,
        INSTRUCTIONS_DIR / "python.instructions.md",
        INSTRUCTIONS_DIR / "scripts.instructions.md",
    ]
    for path in files_to_check:
        content = path.read_text(encoding="utf-8")
        # Check for specific class name OR general term (case-insensitive)
        has_primitive_guidance = "RetryPrimitive" in content or "primitives" in content.lower()
        assert has_primitive_guidance, f"{path.name} should mention primitives usage"


def test_consistent_python_version():
    """All files referencing Python version should agree on 3.12+."""
    main_content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    python_content = (INSTRUCTIONS_DIR / "python.instructions.md").read_text(encoding="utf-8")

    assert "3.12" in main_content, "Main instructions should specify Python 3.12+"
    assert "3.12" in python_content, "Python instructions should specify Python 3.12+"


def test_consistent_type_hint_style():
    """All files should agree on modern type hint style."""
    main_content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    python_content = (INSTRUCTIONS_DIR / "python.instructions.md").read_text(encoding="utf-8")

    for content, name in [
        (main_content, "copilot-instructions"),
        (python_content, "python"),
    ]:
        assert "str | None" in content, f"{name} should use 'str | None' style"
        assert "Optional[str]" in content, f"{name} should warn against Optional[str]"


def test_consistent_formatter_guidance():
    """Files referencing formatting should agree on Ruff."""
    main_content = COPILOT_INSTRUCTIONS.read_text(encoding="utf-8")
    python_content = (INSTRUCTIONS_DIR / "python.instructions.md").read_text(encoding="utf-8")

    for content, name in [
        (main_content, "copilot-instructions"),
        (python_content, "python"),
    ]:
        assert "ruff" in content.lower(), f"{name} should reference Ruff formatter"


def test_no_conflicting_line_lengths():
    """All files mentioning line length should agree on 88 characters (matching pyproject.toml)."""
    for path in [COPILOT_INSTRUCTIONS, INSTRUCTIONS_DIR / "python.instructions.md"]:
        content = path.read_text(encoding="utf-8")
        if "line length" in content.lower() or "line_length" in content.lower():
            assert "88" in content, (
                f"{path.name}: line length should be 88 (matches pyproject.toml)"
            )


def test_anti_pattern_examples_present():
    """Files with anti-pattern sections should show both ✅ and ❌ examples."""
    for filename in ["python.instructions.md", "scripts.instructions.md"]:
        content = (INSTRUCTIONS_DIR / filename).read_text(encoding="utf-8")
        assert "✅" in content, f"{filename}: should have ✅ (correct) examples"
        assert "❌" in content, f"{filename}: should have ❌ (wrong) examples"
