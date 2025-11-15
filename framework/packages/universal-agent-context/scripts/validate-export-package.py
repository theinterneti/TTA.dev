#!/usr/bin/env python3
"""
Validation script for Universal Agent Context System export package.

This script validates:
1. YAML frontmatter in instruction files
2. YAML frontmatter in chat mode files
3. File structure and required files
4. Cross-references and links
5. Schema compliance

Usage:
    python scripts/validate-export-package.py
    python scripts/validate-export-package.py --strict
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class ExportPackageValidator:
    """Validator for Universal Agent Context System export package."""

    def __init__(self, root_dir: Path, strict: bool = False):
        self.root_dir = root_dir
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_all(self) -> bool:
        """Run all validations."""
        print("🔍 Validating Universal Agent Context System export package...\n")

        # Validate file structure
        self.validate_file_structure()

        # Validate instruction files
        self.validate_instruction_files()

        # Validate chat mode files
        self.validate_chat_mode_files()

        # Validate core files
        self.validate_core_files()

        # Validate cross-references
        self.validate_cross_references()

        # Print results
        self.print_results()

        return len(self.errors) == 0

    def validate_file_structure(self):
        """Validate required directory structure."""
        print("📁 Validating file structure...")

        required_dirs = [
            ".github/instructions",
            ".github/chatmodes",
        ]

        for dir_path in required_dirs:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                self.errors.append(f"Missing required directory: {dir_path}")
            elif not full_path.is_dir():
                self.errors.append(f"Not a directory: {dir_path}")

        required_files = [
            "AGENTS.md",
            "apm.yml",
            "README.md",
            "INTEGRATION_GUIDE.md",
            "YAML_SCHEMA.md",
            "MIGRATION_GUIDE.md",
        ]

        for file_path in required_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                self.errors.append(f"Missing required file: {file_path}")
            elif not full_path.is_file():
                self.errors.append(f"Not a file: {file_path}")

    def validate_instruction_files(self):
        """Validate instruction files with YAML frontmatter."""
        print("📝 Validating instruction files...")

        instructions_dir = self.root_dir / ".github" / "instructions"
        if not instructions_dir.exists():
            return

        instruction_files = list(instructions_dir.glob("*.instructions.md"))
        if not instruction_files:
            self.warnings.append("No instruction files found in .github/instructions/")
            return

        for file_path in instruction_files:
            self.validate_instruction_file(file_path)

    def validate_instruction_file(self, file_path: Path):
        """Validate a single instruction file."""
        try:
            content = file_path.read_text()
            frontmatter, body = self.extract_frontmatter(content)

            if not frontmatter:
                self.errors.append(f"{file_path.name}: Missing YAML frontmatter")
                return

            # Validate required fields
            required_fields = ["applyTo", "tags", "description"]
            for field in required_fields:
                if field not in frontmatter:
                    self.errors.append(f"{file_path.name}: Missing required field '{field}'")

            # Validate applyTo patterns
            if "applyTo" in frontmatter:
                if not isinstance(frontmatter["applyTo"], list):
                    self.errors.append(f"{file_path.name}: 'applyTo' must be a list")
                else:
                    for item in frontmatter["applyTo"]:
                        if not isinstance(item, dict) or "pattern" not in item:
                            self.errors.append(f"{file_path.name}: Invalid 'applyTo' item format")

            # Validate tags
            if "tags" in frontmatter:
                if not isinstance(frontmatter["tags"], list):
                    self.errors.append(f"{file_path.name}: 'tags' must be a list")
                else:
                    for tag in frontmatter["tags"]:
                        if not isinstance(tag, str) or not re.match(r"^[a-z0-9-]+$", tag):
                            self.errors.append(f"{file_path.name}: Invalid tag format '{tag}'")

            # Validate priority (if present)
            if "priority" in frontmatter:
                priority = frontmatter["priority"]
                if not isinstance(priority, int) or not (1 <= priority <= 10):
                    self.errors.append(f"{file_path.name}: Priority must be integer 1-10")

            # Validate version (if present)
            if "version" in frontmatter:
                version = frontmatter["version"]
                if not re.match(r"^\d+\.\d+\.\d+$", str(version)):
                    self.errors.append(f"{file_path.name}: Invalid version format (use semver)")

        except Exception as e:
            self.errors.append(f"{file_path.name}: Validation error - {str(e)}")

    def validate_chat_mode_files(self):
        """Validate chat mode files with YAML frontmatter."""
        print("🤖 Validating chat mode files...")

        chatmodes_dir = self.root_dir / ".github" / "chatmodes"
        if not chatmodes_dir.exists():
            return

        chatmode_files = list(chatmodes_dir.glob("*.chatmode.md"))
        if not chatmode_files:
            self.warnings.append("No chat mode files found in .github/chatmodes/")
            return

        for file_path in chatmode_files:
            self.validate_chat_mode_file(file_path)

    def validate_chat_mode_file(self, file_path: Path):
        """Validate a single chat mode file."""
        try:
            content = file_path.read_text()
            frontmatter, body = self.extract_frontmatter(content)

            if not frontmatter:
                self.errors.append(f"{file_path.name}: Missing YAML frontmatter")
                return

            # Validate required fields
            required_fields = ["mode", "description", "cognitive_focus", "security_level"]
            for field in required_fields:
                if field not in frontmatter:
                    self.errors.append(f"{file_path.name}: Missing required field '{field}'")

            # Validate mode format
            if "mode" in frontmatter:
                mode = frontmatter["mode"]
                if not re.match(r"^[a-z0-9-]+$", mode):
                    self.errors.append(
                        f"{file_path.name}: Invalid mode format (use lowercase-with-hyphens)"
                    )

            # Validate security level
            if "security_level" in frontmatter:
                security_level = frontmatter["security_level"]
                if security_level not in ["LOW", "MEDIUM", "HIGH"]:
                    self.errors.append(
                        f"{file_path.name}: Invalid security_level (must be LOW, MEDIUM, or HIGH)"
                    )

            # Validate tool lists (if present)
            if "allowed_tools" in frontmatter and "denied_tools" in frontmatter:
                allowed = set(frontmatter["allowed_tools"])
                denied = set(frontmatter["denied_tools"])
                overlap = allowed & denied
                if overlap:
                    self.errors.append(
                        f"{file_path.name}: Tools in both allowed and denied: {overlap}"
                    )

        except Exception as e:
            self.errors.append(f"{file_path.name}: Validation error - {str(e)}")

    def validate_core_files(self):
        """Validate core files (AGENTS.md, apm.yml, etc.)."""
        print("📄 Validating core files...")

        # Validate AGENTS.md
        agents_md = self.root_dir / "AGENTS.md"
        if agents_md.exists():
            content = agents_md.read_text()
            if "# TTA" in content and self.strict:
                self.warnings.append(
                    "AGENTS.md contains TTA-specific content (should be generic for export)"
                )

        # Validate apm.yml
        apm_yml = self.root_dir / "apm.yml"
        if apm_yml.exists():
            try:
                with open(apm_yml) as f:
                    apm_config = yaml.safe_load(f)

                required_fields = ["name", "version", "description"]
                for field in required_fields:
                    if field not in apm_config:
                        self.errors.append(f"apm.yml: Missing required field '{field}'")

            except yaml.YAMLError as e:
                self.errors.append(f"apm.yml: Invalid YAML - {str(e)}")

    def validate_cross_references(self):
        """Validate cross-references between files."""
        print("🔗 Validating cross-references...")

        # Check that referenced files exist
        agents_md = self.root_dir / "AGENTS.md"
        if agents_md.exists():
            content = agents_md.read_text()

            # Check for references to other files
            references = [
                ("CLAUDE.md", "CLAUDE.md"),
                ("GEMINI.md", "GEMINI.md"),
                (".github/copilot-instructions.md", ".github/copilot-instructions.md"),
            ]

            for ref_text, ref_file in references:
                if ref_text in content:
                    ref_path = self.root_dir / ref_file
                    if not ref_path.exists():
                        self.warnings.append(
                            f"AGENTS.md references {ref_file} but file doesn't exist"
                        )

    def extract_frontmatter(self, content: str) -> tuple[dict, str]:
        """Extract YAML frontmatter from markdown content."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if not match:
            return {}, content

        frontmatter_text = match.group(1)
        body = match.group(2)

        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            return frontmatter or {}, body
        except yaml.YAMLError:
            return {}, content

    def print_results(self):
        """Print validation results."""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60 + "\n")

        if self.errors:
            print(f"❌ {len(self.errors)} ERROR(S) FOUND:\n")
            for error in self.errors:
                print(f"  ❌ {error}")
            print()

        if self.warnings:
            print(f"⚠️  {len(self.warnings)} WARNING(S) FOUND:\n")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ ALL VALIDATIONS PASSED!\n")
            print("Export package is ready for distribution.\n")
        elif not self.errors:
            print("✅ NO ERRORS FOUND (warnings can be ignored)\n")
            print("Export package is ready for distribution.\n")
        else:
            print("❌ VALIDATION FAILED\n")
            print("Please fix errors before exporting.\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Universal Agent Context System export package"
    )
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="Root directory of export package"
    )
    parser.add_argument("--strict", action="store_true", help="Enable strict validation mode")
    args = parser.parse_args()

    validator = ExportPackageValidator(args.root, strict=args.strict)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
