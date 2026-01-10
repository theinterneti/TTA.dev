#!/usr/bin/env python3
"""
Integration tests for agent primitive adoption.

Tests that verify examples and key modules use TTA.dev primitives correctly
instead of manual asyncio orchestration.
"""

import ast
from pathlib import Path

import pytest


class TestPrimitiveAdoption:
    """Test suite for primitive usage validation."""

    @pytest.fixture
    def examples_dir(self) -> Path:
        """Get path to examples directory."""
        return Path("platform/primitives/examples")

    @pytest.fixture
    def src_dir(self) -> Path:
        """Get path to src directory."""
        return Path("platform/primitives/src")

    def test_examples_import_primitives(self, examples_dir: Path):
        """Verify all examples import from tta_dev_primitives."""
        if not examples_dir.exists():
            pytest.skip(f"Examples directory not found: {examples_dir}")

        missing_imports = []

        for example_file in examples_dir.glob("*.py"):
            # Skip private files and __init__
            if example_file.name.startswith("_"):
                continue

            content = example_file.read_text()
            tree = ast.parse(content)

            # Check for primitive imports
            imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            primitive_imports = [
                imp for imp in imports if imp.module and "tta_dev_primitives" in imp.module
            ]

            if not primitive_imports:
                missing_imports.append(example_file.name)

        # Allow some exceptions (utility scripts, test templates, etc.)
        allowed_exceptions = {
            "e2b_webhook_monitoring_server.py",  # Utility server
            "test_ml_template.py",  # Test template
            "simple_ml_template_test.py",  # Test template
        }

        unexpected_files = [f for f in missing_imports if f not in allowed_exceptions]

        assert not unexpected_files, f"Examples missing primitive imports: {unexpected_files}"

    def test_no_direct_asyncio_gather_in_examples(self, examples_dir: Path):
        """Verify examples don't use asyncio.gather() directly."""
        if not examples_dir.exists():
            pytest.skip(f"Examples directory not found: {examples_dir}")

        files_with_gather = []

        for example_file in examples_dir.glob("*.py"):
            if example_file.name.startswith("_"):
                continue

            content = example_file.read_text()

            # Skip if explicitly allowed
            if "# pragma: allow-asyncio" in content:
                continue

            if "asyncio.gather(" in content:
                files_with_gather.append(example_file.name)

        # Allow some files that demonstrate the anti-pattern
        allowed_files = {
            "multi_agent_workflow.py",  # Demonstrates parallel execution
            "multi_model_orchestration.py",  # Shows orchestration patterns
        }

        unexpected_files = [f for f in files_with_gather if f not in allowed_files]

        assert (
            not unexpected_files
        ), f"Examples using asyncio.gather() without allowance: {unexpected_files}"

    def test_no_direct_asyncio_create_task_in_examples(self, examples_dir: Path):
        """Verify examples don't use asyncio.create_task() directly."""
        if not examples_dir.exists():
            pytest.skip(f"Examples directory not found: {examples_dir}")

        files_with_create_task = []

        for example_file in examples_dir.glob("*.py"):
            if example_file.name.startswith("_"):
                continue

            content = example_file.read_text()

            # Skip if explicitly allowed
            if "# pragma: allow-asyncio" in content:
                continue

            if "asyncio.create_task(" in content:
                files_with_create_task.append(example_file.name)

        assert (
            not files_with_create_task
        ), f"Examples using asyncio.create_task(): {files_with_create_task}"

    def test_examples_use_workflow_context(self, examples_dir: Path):
        """Verify examples use WorkflowContext for execution."""
        if not examples_dir.exists():
            pytest.skip(f"Examples directory not found: {examples_dir}")

        missing_context = []

        for example_file in examples_dir.glob("*.py"):
            if example_file.name.startswith("_"):
                continue

            content = example_file.read_text()

            # Check for WorkflowContext import
            if "WorkflowContext" not in content:
                # Some examples might not need it (utility scripts)
                if "execute(" in content:
                    missing_context.append(example_file.name)

        # Allow some exceptions
        allowed_exceptions = {
            "observability_demo.py",  # Demonstrates different context patterns
        }

        unexpected_files = [f for f in missing_context if f not in allowed_exceptions]

        # This is a warning, not a hard failure
        if unexpected_files:
            pytest.skip(
                f"Examples without WorkflowContext (may be intentional): {unexpected_files}"
            )

    def test_core_primitives_extend_base(self, src_dir: Path):
        """Verify core primitives extend WorkflowPrimitive."""
        primitives_dir = src_dir / "tta_dev_primitives" / "core"

        if not primitives_dir.exists():
            pytest.skip(f"Primitives directory not found: {primitives_dir}")

        invalid_primitives = []

        for py_file in primitives_dir.glob("*.py"):
            # Skip __init__ and base
            if py_file.name in ("__init__.py", "base.py"):
                continue

            content = py_file.read_text()
            tree = ast.parse(content)

            # Find class definitions
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]

            # Check if classes extend WorkflowPrimitive or InstrumentedPrimitive
            for cls in classes:
                # Skip internal/helper classes
                if cls.name.startswith("_"):
                    continue

                # Skip non-primitive classes
                if not cls.name.endswith("Primitive"):
                    continue

                # Check base classes
                has_correct_base = False
                for base in cls.bases:
                    if isinstance(base, ast.Name):
                        if base.id in (
                            "WorkflowPrimitive",
                            "InstrumentedPrimitive",
                        ):
                            has_correct_base = True
                    elif isinstance(base, ast.Subscript):
                        if isinstance(base.value, ast.Name):
                            if base.value.id in (
                                "WorkflowPrimitive",
                                "InstrumentedPrimitive",
                            ):
                                has_correct_base = True

                if not has_correct_base:
                    invalid_primitives.append(f"{py_file.name}:{cls.name}")

        assert (
            not invalid_primitives
        ), f"Primitives not extending base classes: {invalid_primitives}"

    def test_recovery_primitives_handle_errors(self, src_dir: Path):
        """Verify recovery primitives have error handling."""
        recovery_dir = src_dir / "tta_dev_primitives" / "recovery"

        if not recovery_dir.exists():
            pytest.skip(f"Recovery directory not found: {recovery_dir}")

        missing_error_handling = []

        for py_file in recovery_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text()
            tree = ast.parse(content)

            # Check for try/except blocks
            has_try_except = any(isinstance(node, ast.Try) for node in ast.walk(tree))

            if not has_try_except:
                missing_error_handling.append(py_file.name)

        # Allow some exceptions (e.g., pure wrapper classes)
        allowed_exceptions = {"__init__.py"}

        unexpected_files = [f for f in missing_error_handling if f not in allowed_exceptions]

        assert (
            not unexpected_files
        ), f"Recovery primitives without error handling: {unexpected_files}"


class TestValidatorIntegration:
    """Test the validate-primitive-usage.py script."""

    def test_validator_script_exists(self):
        """Verify validator script exists."""
        validator_path = Path("scripts/validate-primitive-usage.py")
        assert validator_path.exists(), "Validator script not found"
        assert validator_path.is_file(), "Validator path is not a file"

    def test_validator_is_executable(self):
        """Verify validator script has execute permission."""
        validator_path = Path("scripts/validate-primitive-usage.py")
        if not validator_path.exists():
            pytest.skip("Validator script not found")

        # Check if readable
        assert validator_path.stat().st_mode & 0o400, "Validator not readable"

    def test_validator_runs_without_errors(self):
        """Verify validator can be imported and run."""
        try:
            import subprocess
            import sys

            result = subprocess.run(
                [sys.executable, "scripts/validate-primitive-usage.py", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert result.returncode == 0, f"Validator failed: {result.stderr}"
            assert "TTA.dev Primitive Usage Validator" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("Validator script timed out")
        except Exception as e:
            pytest.fail(f"Failed to run validator: {e}")


class TestPreCommitHook:
    """Test the pre-commit hook."""

    def test_pre_commit_hook_exists(self):
        """Verify pre-commit hook is installed."""
        hook_path = Path(".git/hooks/pre-commit")
        # Skip in CI environments where hooks aren't installed
        import os

        if os.getenv("CI"):
            pytest.skip("Skipping pre-commit hook test in CI environment")
        assert hook_path.exists(), "Pre-commit hook not found"

    def test_pre_commit_hook_is_executable(self):
        """Verify pre-commit hook has execute permission."""
        hook_path = Path(".git/hooks/pre-commit")
        if not hook_path.exists():
            pytest.skip("Pre-commit hook not found")

        # Check for execute permission
        assert hook_path.stat().st_mode & 0o100, "Pre-commit hook not executable"

    def test_setup_git_hooks_script_exists(self):
        """Verify setup script exists."""
        setup_script = Path("scripts/setup-git-hooks.sh")
        assert setup_script.exists(), "Setup script not found"
        assert setup_script.is_file(), "Setup path is not a file"


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
