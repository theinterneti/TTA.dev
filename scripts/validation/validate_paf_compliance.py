#!/usr/bin/env python3
"""
Validate PAF (Permanent Architectural Facts) compliance across the project.

This script validates architectural constraints defined in PAFCORE.md
to ensure the codebase adheres to permanent architectural decisions.

Usage:
    python scripts/validation/validate_paf_compliance.py [--strict]

Exit codes:
    0: All PAF validations passed
    1: One or more PAF validations failed (warnings)
    2: Critical PAF validations failed (errors)
"""

import argparse
import sys
from pathlib import Path

# Add project packages to path for local imports
project_root = Path(__file__).parent.parent.parent
packages_path = project_root / "packages" / "tta-dev-primitives" / "src"
sys.path.insert(0, str(packages_path))

from tta_dev_primitives import PAFMemoryPrimitive, PAFValidationResult  # noqa: E402


class PAFComplianceValidator:
    """Validator for PAF compliance across the project."""

    def __init__(self, strict: bool = False):
        """
        Initialize PAF compliance validator.

        Args:
            strict: If True, treat warnings as errors
        """
        self.paf = PAFMemoryPrimitive()
        self.strict = strict
        self.results: list[PAFValidationResult] = []
        self.errors = 0
        self.warnings = 0

    def validate_python_version(self) -> None:
        """Validate Python version against PAF-LANG-001."""
        import platform

        version = platform.python_version()
        result = self.paf.validate_python_version(version)
        self._record_result("Python Version (LANG-001)", result)

    def validate_test_coverage(self) -> None:
        """Validate test coverage against PAF-QUAL-001."""
        # Try to get coverage from coverage.xml if it exists
        coverage_file = project_root / "coverage.xml"

        if not coverage_file.exists():
            print("⚠️  Coverage file not found, skipping coverage validation")
            return

        # Parse coverage percentage from coverage.xml
        import xml.etree.ElementTree as ET

        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            coverage_element = root.find(".//coverage")

            if coverage_element is not None:
                line_rate = float(coverage_element.get("line-rate", 0))
                coverage_percent = line_rate * 100
                result = self.paf.validate_test_coverage(coverage_percent)
                self._record_result("Test Coverage (QUAL-001)", result)
            else:
                print("⚠️  Could not parse coverage percentage")
        except Exception as e:
            print(f"⚠️  Error parsing coverage: {e}")

    def validate_file_sizes(self) -> None:
        """Validate file sizes against PAF-QUAL-002."""
        # Check all Python files in packages/
        packages_dir = project_root / "packages"

        if not packages_dir.exists():
            return

        violations = []

        for py_file in packages_dir.rglob("*.py"):
            # Skip __init__.py and test files
            if py_file.name == "__init__.py" or "test" in py_file.name:
                continue

            # Count lines
            try:
                lines = len(py_file.read_text().splitlines())
                result = self.paf.validate_file_size(py_file, lines)

                if not result.is_valid:
                    violations.append(
                        f"  • {py_file.relative_to(project_root)}: {lines} lines"
                    )
                    self._record_result(f"File Size: {py_file.name}", result)

            except Exception:
                continue

        if violations:
            print("\n📏 File size violations (QUAL-002):")
            for violation in violations[:10]:  # Show first 10
                print(violation)
            if len(violations) > 10:
                print(f"  ... and {len(violations) - 10} more")

    def validate_package_manager(self) -> None:
        """Validate package manager against PAF-LANG-002."""
        # Check if uv.lock exists
        uv_lock = project_root / "uv.lock"

        result = self.paf.validate_against_paf(
            "LANG-002", "uv", lambda value, paf: uv_lock.exists()
        )
        self._record_result("Package Manager (LANG-002)", result)

    def validate_paf_core_exists(self) -> None:
        """Validate PAFCORE.md exists and is parseable."""
        paf_core_path = project_root / ".universal-instructions" / "paf" / "PAFCORE.md"

        # Check file exists
        if not paf_core_path.exists():
            result = PAFValidationResult(
                paf_id="PAFCORE",
                is_valid=False,
                actual_value="missing",
                expected_value="exists",
                reason="PAFCORE.md not found at .universal-instructions/paf/",
                severity="error",
            )
            self._record_result("PAFCORE.md Exists", result)
            return

        # Check PAFs loaded
        pafs = self.paf.get_all_pafs()
        if len(pafs) == 0:
            result = PAFValidationResult(
                paf_id="PAFCORE",
                is_valid=False,
                actual_value="0 PAFs",
                expected_value=">0 PAFs",
                reason="PAFCORE.md contains no PAFs",
                severity="error",
            )
        else:
            result = PAFValidationResult(
                paf_id="PAFCORE",
                is_valid=True,
                actual_value=f"{len(pafs)} PAFs loaded",
                expected_value=">0 PAFs",
                severity="info",
            )

        self._record_result("PAFCORE.md Loaded", result)

    def _record_result(self, check_name: str, result: PAFValidationResult) -> None:
        """Record validation result and update counters."""
        self.results.append(result)

        if not result.is_valid:
            if result.severity == "error" or self.strict:
                self.errors += 1
                print(f"❌ {check_name}: {result.reason}")
            else:
                self.warnings += 1
                print(f"⚠️  {check_name}: {result.reason}")
        else:
            print(f"✅ {check_name}")

    def run_all_validations(self) -> int:
        """
        Run all PAF validations.

        Returns:
            Exit code: 0 = success, 1 = warnings, 2 = errors
        """
        print("🔍 Running PAF Compliance Validations...\n")

        # Core validations
        self.validate_paf_core_exists()
        self.validate_python_version()
        self.validate_package_manager()
        self.validate_test_coverage()
        self.validate_file_sizes()

        # Summary
        print("\n" + "=" * 50)
        print("📊 PAF Validation Summary")
        print("=" * 50)

        active_pafs = self.paf.get_active_pafs()
        print(f"Total Active PAFs: {len(active_pafs)}")
        print(f"Validations Run: {len(self.results)}")
        print(f"Passed: {len([r for r in self.results if r.is_valid])}")
        print(f"Warnings: {self.warnings}")
        print(f"Errors: {self.errors}")

        if self.errors > 0:
            print("\n❌ PAF validation failed with errors")
            return 2
        elif self.warnings > 0:
            print("\n⚠️  PAF validation passed with warnings")
            return 1
        else:
            print("\n✅ All PAF validations passed")
            return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate PAF compliance across the project"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )

    args = parser.parse_args()

    validator = PAFComplianceValidator(strict=args.strict)
    return validator.run_all_validations()


if __name__ == "__main__":
    sys.exit(main())
