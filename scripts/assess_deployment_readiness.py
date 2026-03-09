"""Readiness Assessment for TTA.dev MCP Server Deployment.

This script implements the meta-framework concept: it knows what "production ready" means
and can validate if we're ready to deploy to GitHub's MCP Registry.

Usage:
    uv run python scripts/assess_deployment_readiness.py --target mcp-servers

This is the beginning of the guided workflow system you envisioned!
"""

import argparse
import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Stage(Enum):
    """Development lifecycle stages."""

    EXPERIMENTATION = "experimentation"
    TESTING = "testing"
    STAGING = "staging"
    DEPLOYMENT = "deployment"
    PRODUCTION = "production"


class Severity(Enum):
    """Issue severity levels."""

    BLOCKER = "blocker"  # Must fix before proceeding
    CRITICAL = "critical"  # Should fix before proceeding
    WARNING = "warning"  # Nice to fix but not required
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    passed: bool
    severity: Severity
    message: str
    fix_command: str | None = None
    documentation: str | None = None


@dataclass
class StageReadiness:
    """Readiness assessment for a development stage."""

    current_stage: Stage
    target_stage: Stage
    ready: bool
    blockers: list[ValidationResult]
    critical_issues: list[ValidationResult]
    warnings: list[ValidationResult]
    info: list[ValidationResult]
    next_steps: list[str]


class DeploymentReadinessChecker:
    """Validates if a package is ready for deployment to GitHub MCP Registry."""

    def __init__(self, package_path: Path, verbose: bool = False):
        self.package_path = package_path
        self.verbose = verbose
        self.results: list[ValidationResult] = []

    async def check_all(self) -> StageReadiness:
        """Run all validation checks."""
        print(f"\n🔍 Assessing deployment readiness for: {self.package_path.name}")
        print("=" * 80)

        # Check if package exists
        if not self.package_path.exists():
            return self._package_not_found()

        # Run all validation checks
        await self._check_package_structure()
        await self._check_dependencies()
        await self._check_tests()
        await self._check_type_coverage()
        await self._check_documentation()
        await self._check_examples()
        await self._check_mcp_manifest()
        await self._check_license()
        await self._check_ci_cd()
        await self._check_git_status()

        # Categorize results
        blockers = [
            r for r in self.results if not r.passed and r.severity == Severity.BLOCKER
        ]
        critical = [
            r for r in self.results if not r.passed and r.severity == Severity.CRITICAL
        ]
        warnings = [
            r for r in self.results if not r.passed and r.severity == Severity.WARNING
        ]
        info_items = [r for r in self.results if r.severity == Severity.INFO]

        # Determine readiness
        ready = len(blockers) == 0 and len(critical) == 0

        # Generate next steps
        next_steps = self._generate_next_steps(blockers, critical, warnings)

        return StageReadiness(
            current_stage=Stage.EXPERIMENTATION if not ready else Stage.STAGING,
            target_stage=Stage.DEPLOYMENT,
            ready=ready,
            blockers=blockers,
            critical_issues=critical,
            warnings=warnings,
            info=info_items,
            next_steps=next_steps,
        )

    def _package_not_found(self) -> StageReadiness:
        """Handle case where package doesn't exist yet."""
        return StageReadiness(
            current_stage=Stage.EXPERIMENTATION,
            target_stage=Stage.DEPLOYMENT,
            ready=False,
            blockers=[
                ValidationResult(
                    name="Package Exists",
                    passed=False,
                    severity=Severity.BLOCKER,
                    message=f"Package not found at {self.package_path}",
                    fix_command="Create the package structure first",
                    documentation="See GITHUB_ISSUES_MCP_SERVERS.md Issue #1",
                )
            ],
            critical_issues=[],
            warnings=[],
            info=[],
            next_steps=[
                "📦 Create package structure (see Issue #1)",
                "✅ Implement core functionality",
                "🧪 Write tests",
                "📝 Write documentation",
                "🔄 Run this check again",
            ],
        )

    async def _check_package_structure(self) -> None:
        """Check if package has required structure."""
        required_files = {
            "pyproject.toml": Severity.BLOCKER,
            "README.md": Severity.CRITICAL,
            "CHANGELOG.md": Severity.WARNING,
            "LICENSE": Severity.CRITICAL,
            "src": Severity.BLOCKER,
            "tests": Severity.BLOCKER,
        }

        for file, severity in required_files.items():
            path = self.package_path / file
            exists = path.exists()

            self.results.append(
                ValidationResult(
                    name=f"Has {file}",
                    passed=exists,
                    severity=severity,
                    message=f"{'✓' if exists else '✗'} {file} {'exists' if exists else 'missing'}",
                    fix_command=f"Create {file}" if not exists else None,
                )
            )

    async def _check_dependencies(self) -> None:
        """Check if dependencies are properly declared."""
        pyproject = self.package_path / "pyproject.toml"
        if not pyproject.exists():
            return

        content = pyproject.read_text()
        has_fastmcp = "fastmcp" in content
        has_tta_primitives = "tta-dev-primitives" in content

        self.results.append(
            ValidationResult(
                name="FastMCP Dependency",
                passed=has_fastmcp,
                severity=Severity.BLOCKER,
                message=f"{'✓' if has_fastmcp else '✗'} fastmcp dependency declared",
                fix_command="uv add fastmcp" if not has_fastmcp else None,
            )
        )

        self.results.append(
            ValidationResult(
                name="TTA Primitives Dependency",
                passed=has_tta_primitives,
                severity=Severity.BLOCKER,
                message=f"{'✓' if has_tta_primitives else '✗'} tta-dev-primitives dependency declared",
                fix_command="uv add tta-dev-primitives"
                if not has_tta_primitives
                else None,
            )
        )

    async def _check_tests(self) -> None:
        """Check if tests exist and pass."""
        tests_dir = self.package_path / "tests"
        if not tests_dir.exists():
            self.results.append(
                ValidationResult(
                    name="Tests Exist",
                    passed=False,
                    severity=Severity.BLOCKER,
                    message="✗ No tests directory found",
                    fix_command="mkdir tests && touch tests/test_server.py",
                )
            )
            return

        # Check if test files exist
        test_files = list(tests_dir.glob("test_*.py"))
        has_tests = len(test_files) > 0

        self.results.append(
            ValidationResult(
                name="Tests Exist",
                passed=has_tests,
                severity=Severity.BLOCKER,
                message=f"{'✓' if has_tests else '✗'} Found {len(test_files)} test files",
                fix_command="Create test files in tests/" if not has_tests else None,
            )
        )

        if not has_tests:
            return

        # Try to run tests
        try:
            result = subprocess.run(
                ["uv", "run", "pytest", str(tests_dir), "-v"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            tests_pass = result.returncode == 0

            self.results.append(
                ValidationResult(
                    name="Tests Pass",
                    passed=tests_pass,
                    severity=Severity.BLOCKER,
                    message=f"{'✓' if tests_pass else '✗'} Tests {'pass' if tests_pass else 'fail'}",
                    fix_command="Fix failing tests" if not tests_pass else None,
                )
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.results.append(
                ValidationResult(
                    name="Tests Pass",
                    passed=False,
                    severity=Severity.BLOCKER,
                    message=f"✗ Could not run tests: {e}",
                )
            )

    async def _check_type_coverage(self) -> None:
        """Check if code has type annotations."""
        src_dir = self.package_path / "src"
        if not src_dir.exists():
            return

        try:
            result = subprocess.run(
                ["uvx", "pyright", str(src_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            type_check_passes = result.returncode == 0

            self.results.append(
                ValidationResult(
                    name="Type Check Passes",
                    passed=type_check_passes,
                    severity=Severity.CRITICAL,
                    message=f"{'✓' if type_check_passes else '✗'} Type checking {'passes' if type_check_passes else 'fails'}",
                    fix_command="Add type hints and fix type errors"
                    if not type_check_passes
                    else None,
                )
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results.append(
                ValidationResult(
                    name="Type Check Passes",
                    passed=False,
                    severity=Severity.WARNING,
                    message="⚠ Could not run pyright",
                )
            )

    async def _check_documentation(self) -> None:
        """Check if documentation is complete."""
        readme = self.package_path / "README.md"
        if not readme.exists():
            return

        content = readme.read_text()
        required_sections = {
            "Installation": Severity.CRITICAL,
            "Usage": Severity.CRITICAL,
            "Quick Start": Severity.CRITICAL,
            "Examples": Severity.WARNING,
            "API": Severity.WARNING,
            "Contributing": Severity.INFO,
        }

        for section, severity in required_sections.items():
            has_section = section.lower() in content.lower()

            self.results.append(
                ValidationResult(
                    name=f"README has {section} section",
                    passed=has_section,
                    severity=severity,
                    message=f"{'✓' if has_section else '✗'} {section} section in README",
                    fix_command=f"Add {section} section to README.md"
                    if not has_section
                    else None,
                )
            )

    async def _check_examples(self) -> None:
        """Check if examples exist."""
        examples_dir = self.package_path / "examples"
        has_examples = (
            examples_dir.exists() and len(list(examples_dir.glob("*.py"))) > 0
        )

        self.results.append(
            ValidationResult(
                name="Examples Exist",
                passed=has_examples,
                severity=Severity.CRITICAL,
                message=f"{'✓' if has_examples else '✗'} Example code {'exists' if has_examples else 'missing'}",
                fix_command="Create examples/ directory with working examples"
                if not has_examples
                else None,
            )
        )

    async def _check_mcp_manifest(self) -> None:
        """Check if MCP manifest exists and is valid."""
        manifest = self.package_path / "mcp-manifest.json"
        has_manifest = manifest.exists()

        self.results.append(
            ValidationResult(
                name="MCP Manifest Exists",
                passed=has_manifest,
                severity=Severity.BLOCKER,
                message=f"{'✓' if has_manifest else '✗'} mcp-manifest.json {'exists' if has_manifest else 'missing'}",
                fix_command="Create mcp-manifest.json" if not has_manifest else None,
                documentation="See GITHUB_ISSUES_MCP_SERVERS.md for manifest schema",
            )
        )

        if not has_manifest:
            return

        # Validate manifest structure
        try:
            manifest_data = json.loads(manifest.read_text())
            required_fields = ["name", "version", "description", "author", "tools"]

            for field in required_fields:
                has_field = field in manifest_data

                self.results.append(
                    ValidationResult(
                        name=f"Manifest has {field}",
                        passed=has_field,
                        severity=Severity.CRITICAL,
                        message=f"{'✓' if has_field else '✗'} {field} field in manifest",
                        fix_command=f"Add {field} to mcp-manifest.json"
                        if not has_field
                        else None,
                    )
                )
        except json.JSONDecodeError:
            self.results.append(
                ValidationResult(
                    name="Manifest Valid JSON",
                    passed=False,
                    severity=Severity.BLOCKER,
                    message="✗ mcp-manifest.json is not valid JSON",
                    fix_command="Fix JSON syntax in mcp-manifest.json",
                )
            )

    async def _check_license(self) -> None:
        """Check if LICENSE file exists."""
        license_file = self.package_path / "LICENSE"
        has_license = license_file.exists()

        self.results.append(
            ValidationResult(
                name="License File Exists",
                passed=has_license,
                severity=Severity.CRITICAL,
                message=f"{'✓' if has_license else '✗'} LICENSE file {'exists' if has_license else 'missing'}",
                fix_command="Add LICENSE file (MIT or Apache 2.0 recommended)"
                if not has_license
                else None,
                documentation="GitHub MCP Registry requires a license",
            )
        )

    async def _check_ci_cd(self) -> None:
        """Check if CI/CD is configured."""
        workflows_dir = Path(".github/workflows")
        has_ci = workflows_dir.exists() and len(list(workflows_dir.glob("*.yml"))) > 0

        self.results.append(
            ValidationResult(
                name="CI/CD Configured",
                passed=has_ci,
                severity=Severity.WARNING,
                message=f"{'✓' if has_ci else '⚠'} GitHub Actions {'configured' if has_ci else 'not configured'}",
                fix_command="Add .github/workflows/test.yml" if not has_ci else None,
            )
        )

    async def _check_git_status(self) -> None:
        """Check git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            is_clean = len(result.stdout.strip()) == 0

            self.results.append(
                ValidationResult(
                    name="Git Working Tree Clean",
                    passed=is_clean,
                    severity=Severity.WARNING,
                    message=f"{'✓' if is_clean else '⚠'} Working tree {'clean' if is_clean else 'has uncommitted changes'}",
                    fix_command="git add . && git commit -m 'Prepare for deployment'"
                    if not is_clean
                    else None,
                )
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def _generate_next_steps(
        self,
        blockers: list[ValidationResult],
        critical: list[ValidationResult],
        warnings: list[ValidationResult],
    ) -> list[str]:
        """Generate actionable next steps."""
        steps = []

        if blockers:
            steps.append("🚫 BLOCKERS - Must fix before deployment:")
            for b in blockers:
                if b.fix_command:
                    steps.append(f"   • {b.message}")
                    steps.append(f"     Fix: {b.fix_command}")
                else:
                    steps.append(f"   • {b.message}")

        if critical:
            steps.append("\n⚠️  CRITICAL - Should fix before deployment:")
            for c in critical[:3]:  # Show top 3
                if c.fix_command:
                    steps.append(f"   • {c.message}")
                    steps.append(f"     Fix: {c.fix_command}")

        if warnings:
            steps.append(f"\n💡 {len(warnings)} warnings (optional improvements)")

        if not blockers and not critical:
            steps.extend(
                [
                    "\n✅ READY FOR DEPLOYMENT!",
                    "",
                    "Next steps:",
                    "1. Review GitHub Issues (#1-#8 in GITHUB_ISSUES_MCP_SERVERS.md)",
                    "2. Create GitHub issues: gh issue create --title '...'",
                    "3. Test locally: code --install-mcp ./path/to/package",
                    "4. Submit to GitHub MCP Registry",
                    "5. Announce on social media",
                ]
            )

        return steps


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Assess deployment readiness for TTA.dev packages"
    )
    parser.add_argument(
        "--target",
        default="mcp-servers",
        help="Target to assess (e.g., 'mcp-servers', 'tta-workflow-primitives-mcp')",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Determine which packages to check
    if args.target == "mcp-servers":
        # Check all planned MCP servers
        packages = [
            Path("packages/tta-workflow-primitives-mcp"),
            Path("packages/tta-observability-mcp"),
            Path("packages/tta-agent-context-mcp"),
        ]
    else:
        packages = [Path(f"packages/{args.target}")]

    all_ready = True
    for package_path in packages:
        checker = DeploymentReadinessChecker(package_path, args.verbose)
        readiness = await checker.check_all()

        # Print results
        print(f"\n📊 RESULTS for {package_path.name}")
        print("=" * 80)
        print(f"Current Stage: {readiness.current_stage.value}")
        print(f"Target Stage: {readiness.target_stage.value}")
        print(f"Ready: {'✅ YES' if readiness.ready else '❌ NO'}")
        print(f"\nBlockers: {len(readiness.blockers)}")
        print(f"Critical Issues: {len(readiness.critical_issues)}")
        print(f"Warnings: {len(readiness.warnings)}")

        print("\n📋 NEXT STEPS")
        print("=" * 80)
        for step in readiness.next_steps:
            print(step)

        if not readiness.ready:
            all_ready = False

    # Exit with appropriate code
    print("\n" + "=" * 80)
    if all_ready:
        print("🎉 All packages ready for deployment!")
        sys.exit(0)
    else:
        print("⚠️  Some packages need work before deployment")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
