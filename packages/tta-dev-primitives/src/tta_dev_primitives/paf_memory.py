"""PAF (Permanent Architectural Facts) Memory Primitive.

This primitive provides access to permanent architectural constraints
stored in PAFCORE.md and validates code against these immutable facts.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class PAFStatus(str, Enum):
    """PAF lifecycle status."""

    PROPOSED = "proposed"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REPLACED = "replaced"


@dataclass
class PAF:
    """Permanent Architectural Fact."""

    category: str  # e.g., "LANG", "PKG", "QUAL"
    fact_id: str  # e.g., "001"
    description: str  # Human-readable description
    status: PAFStatus = PAFStatus.ACTIVE
    deprecated_reason: str | None = None
    replaced_by: str | None = None
    date_added: str | None = None
    date_deprecated: str | None = None

    @property
    def full_id(self) -> str:
        """Get full PAF identifier (e.g., 'LANG-001')."""
        return f"{self.category}-{self.fact_id}"

    def is_active(self) -> bool:
        """Check if PAF is currently active."""
        return self.status == PAFStatus.ACTIVE


@dataclass
class PAFValidationResult:
    """Result of validating against a PAF."""

    paf_id: str
    is_valid: bool
    actual_value: Any
    expected_value: Any | None = None
    reason: str | None = None
    severity: str = "error"  # error, warning, info


class PAFMemoryPrimitive:
    """
    Primitive for loading and validating Permanent Architectural Facts.

    PAFs are atomic, immutable architectural constraints that define
    the permanent foundation of the system.

    Usage:
        paf = PAFMemoryPrimitive()
        result = await paf.validate_python_version("3.12.0")
        if not result.is_valid:
            raise ValueError(f"PAF violation: {result.reason}")
    """

    def __init__(self, paf_core_path: str | Path | None = None) -> None:
        """
        Initialize PAF memory primitive.

        Args:
            paf_core_path: Path to PAFCORE.md (default: .universal-instructions/paf/PAFCORE.md)
        """
        if paf_core_path is None:
            # Try multiple common locations for PAFCORE.md
            possible_paths = [
                # Workspace root (when running from repo root)
                Path.cwd() / ".universal-instructions" / "paf" / "PAFCORE.md",
                # Two levels up from package (when running from packages/tta-dev-primitives)
                Path.cwd() / ".." / ".." / ".universal-instructions" / "paf" / "PAFCORE.md",
                # Docs directory
                Path.cwd() / "docs" / "guides" / "PAFCORE.md",
                # Two levels up then docs
                Path.cwd() / ".." / ".." / "docs" / "guides" / "PAFCORE.md",
            ]

            found_path: Path | None = None
            for path in possible_paths:
                resolved = path.resolve()
                if resolved.exists():
                    found_path = resolved
                    break

            if found_path is None:
                # Default to workspace root for error message
                found_path = Path.cwd() / ".universal-instructions" / "paf" / "PAFCORE.md"

            self.paf_core_path = found_path
        else:
            self.paf_core_path = Path(paf_core_path)

        self.pafs: dict[str, PAF] = {}
        self._load_pafs()

    def _load_pafs(self) -> None:
        """Load PAFs from PAFCORE.md."""
        if not self.paf_core_path.exists():
            raise FileNotFoundError(
                f"PAFCORE.md not found at {self.paf_core_path}. Initialize PAF system first."
            )

        # Parse PAFCORE.md to extract PAF definitions
        # This is a simple parser - could be enhanced with full markdown parsing
        content = self.paf_core_path.read_text()
        lines = content.split("\n")

        current_category = None
        for line in lines:
            # Extract category from headers (e.g., "### 1. Technology Stack")
            if line.startswith("### "):
                # Extract last word as category hint
                category_text = line.replace("###", "").strip()
                if "Technology Stack" in category_text:
                    current_category = "LANG"
                elif "Package Structure" in category_text:
                    current_category = "PKG"
                elif "Code Quality" in category_text:
                    current_category = "QUAL"
                elif "Agent Behavior" in category_text:
                    current_category = "AGENT"
                elif "Development Workflow" in category_text:
                    current_category = "GIT"
                elif "Architecture Patterns" in category_text:
                    current_category = "ARCH"
                elif "Documentation" in category_text:
                    current_category = "DOC"

            # Parse PAF entries (e.g., "- **LANG-001**: Description")
            if line.strip().startswith("- **") and current_category:
                # Extract PAF ID and description
                parts = line.split("**:", 1)
                if len(parts) == 2:
                    paf_id_part = parts[0].replace("- **", "").strip()
                    description = parts[1].strip()

                    # Check if deprecated
                    status = PAFStatus.ACTIVE
                    deprecated_reason = None
                    if "~~" in description or "DEPRECATED" in description:
                        status = PAFStatus.DEPRECATED
                        # Extract deprecated reason if present
                        if "Reason:" in description:
                            deprecated_reason = (
                                description.split("Reason:")[1].split("\n")[0].strip()
                            )

                    # Extract category and fact ID
                    if "-" in paf_id_part:
                        category, fact_id = paf_id_part.split("-", 1)
                        paf = PAF(
                            category=category,
                            fact_id=fact_id,
                            description=description,
                            status=status,
                            deprecated_reason=deprecated_reason,
                        )
                        # Only store active PAFs (skip deprecated ones to avoid duplicates)
                        # Deprecated PAFs are in PAFCORE.md for history but not actively used
                        if status == PAFStatus.ACTIVE:
                            self.pafs[paf.full_id] = paf

    def get_paf(self, paf_id: str) -> PAF | None:
        """
        Get a PAF by its ID.

        Args:
            paf_id: Full PAF ID (e.g., "LANG-001") or partial (e.g., "001" with category context)

        Returns:
            PAF object or None if not found
        """
        return self.pafs.get(paf_id)

    def get_pafs_by_category(self, category: str) -> list[PAF]:
        """
        Get all PAFs in a category.

        Args:
            category: Category code (e.g., "LANG", "PKG", "QUAL")

        Returns:
            List of PAFs in the category
        """
        return [paf for paf in self.pafs.values() if paf.category == category]

    def get_active_pafs(self) -> list[PAF]:
        """Get all active (non-deprecated) PAFs."""
        return [paf for paf in self.pafs.values() if paf.is_active()]

    def validate_python_version(self, version: str) -> PAFValidationResult:
        """
        Validate Python version against PAF-LANG-001.

        Args:
            version: Python version string (e.g., "3.12.0")

        Returns:
            PAFValidationResult
        """
        paf = self.get_paf("LANG-001")
        if not paf:
            return PAFValidationResult(
                paf_id="LANG-001",
                is_valid=False,
                actual_value=version,
                reason="PAF-LANG-001 not found in PAFCORE.md",
                severity="error",
            )

        # Parse version
        try:
            major, minor = map(int, version.split(".")[:2])
            is_valid = (major == 3 and minor >= 12) or major > 3
            return PAFValidationResult(
                paf_id="LANG-001",
                is_valid=is_valid,
                actual_value=version,
                expected_value="Python 3.12+",
                reason=None
                if is_valid
                else f"Python {version} < 3.12 (PAF-LANG-001 requires 3.12+)",
                severity="error",
            )
        except (ValueError, IndexError):
            return PAFValidationResult(
                paf_id="LANG-001",
                is_valid=False,
                actual_value=version,
                expected_value="Python 3.12+",
                reason=f"Invalid version format: {version}",
                severity="error",
            )

    def validate_test_coverage(self, coverage_percent: float) -> PAFValidationResult:
        """
        Validate test coverage against PAF-QUAL-001.

        Args:
            coverage_percent: Test coverage percentage (0-100)

        Returns:
            PAFValidationResult
        """
        paf = self.get_paf("QUAL-001")
        if not paf:
            return PAFValidationResult(
                paf_id="QUAL-001",
                is_valid=False,
                actual_value=coverage_percent,
                reason="PAF-QUAL-001 not found in PAFCORE.md",
                severity="error",
            )

        is_valid = coverage_percent >= 70.0
        return PAFValidationResult(
            paf_id="QUAL-001",
            is_valid=is_valid,
            actual_value=f"{coverage_percent}%",
            expected_value="≥70%",
            reason=None
            if is_valid
            else f"Coverage {coverage_percent}% < 70% (PAF-QUAL-001 requires ≥70%)",
            severity="error" if coverage_percent < 70 else "warning",
        )

    def validate_file_size(self, file_path: Path, line_count: int) -> PAFValidationResult:
        """
        Validate file size against PAF-QUAL-004.

        Args:
            file_path: Path to the file
            line_count: Number of lines in the file

        Returns:
            PAFValidationResult
        """
        paf = self.get_paf("QUAL-004")
        if not paf:
            return PAFValidationResult(
                paf_id="QUAL-004",
                is_valid=False,
                actual_value=line_count,
                reason="PAF-QUAL-004 not found in PAFCORE.md",
                severity="error",
            )

        is_valid = line_count <= 800
        return PAFValidationResult(
            paf_id="QUAL-004",
            is_valid=is_valid,
            actual_value=f"{line_count} lines",
            expected_value="≤800 lines",
            reason=None
            if is_valid
            else f"{file_path.name} has {line_count} lines > 800 (PAF-QUAL-004 limit)",
            severity="warning" if line_count <= 1000 else "error",
        )

    def validate_against_paf(
        self,
        paf_id: str,
        actual_value: str | int | float | bool,
        validator_fn: Callable[[str | int | float | bool, PAF], bool] | None = None,
    ) -> PAFValidationResult:
        """
        Generic PAF validation.

        Args:
            paf_id: Full PAF ID (e.g., "LANG-001")
            actual_value: Actual value to validate
            validator_fn: Optional custom validator function

        Returns:
            PAFValidationResult
        """
        paf = self.get_paf(paf_id)
        if not paf:
            return PAFValidationResult(
                paf_id=paf_id,
                is_valid=False,
                actual_value=actual_value,
                reason=f"{paf_id} not found in PAFCORE.md",
                severity="error",
            )

        if not paf.is_active():
            return PAFValidationResult(
                paf_id=paf_id,
                is_valid=False,
                actual_value=actual_value,
                reason=f"{paf_id} is {paf.status.value}: {paf.deprecated_reason or 'deprecated'}",
                severity="warning",
            )

        # Use custom validator if provided
        if validator_fn:
            is_valid = validator_fn(actual_value, paf)
            return PAFValidationResult(
                paf_id=paf_id,
                is_valid=is_valid,
                actual_value=actual_value,
                reason=None if is_valid else f"Custom validation failed for {paf_id}",
            )

        # Default: just check existence
        return PAFValidationResult(paf_id=paf_id, is_valid=True, actual_value=actual_value)

    def get_all_validations(self) -> list[str]:
        """
        Get list of all PAF validation methods available.

        Returns:
            List of validation method names
        """
        return [
            "validate_python_version",
            "validate_test_coverage",
            "validate_file_size",
            "validate_against_paf",
        ]

    def summary(self) -> dict[str, Any]:
        """
        Get summary of all PAFs.

        Returns:
            Dictionary with PAF statistics and categories
        """
        active_pafs = self.get_active_pafs()
        deprecated_pafs = [paf for paf in self.pafs.values() if not paf.is_active()]

        categories = {}
        for paf in active_pafs:
            if paf.category not in categories:
                categories[paf.category] = 0
            categories[paf.category] += 1

        return {
            "total_pafs": len(self.pafs),
            "active_pafs": len(active_pafs),
            "deprecated_pafs": len(deprecated_pafs),
            "categories": categories,
            "paf_core_path": str(self.paf_core_path),
        }


# Convenience function for quick PAF access
def get_paf_primitive() -> PAFMemoryPrimitive:
    """Get a singleton PAF memory primitive instance."""
    return PAFMemoryPrimitive()
