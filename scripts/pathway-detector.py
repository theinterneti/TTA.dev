#!/usr/bin/env python3
"""
Language Pathway Detector

Automatically detects the primary language(s) used in a project and activates
the appropriate pathway(s).

Usage:
    python pathway-detector.py                    # Detect in current directory
    python pathway-detector.py /path/to/project  # Detect in specific directory
    python pathway-detector.py --all             # Show all detected languages
"""

import json
import sys
from pathlib import Path


class LanguagePathway:
    """Represents a language pathway with detection rules."""

    def __init__(
        self, name: str, markers: list[str], priority: int = 50, description: str = ""
    ):
        self.name = name
        self.markers = markers
        self.priority = priority
        self.description = description
        self.detected_files: list[Path] = []

    def detect(self, project_path: Path) -> bool:
        """Detect if this pathway should be activated."""
        self.detected_files = []
        for marker in self.markers:
            if "*" in marker:
                # Glob pattern
                matches = list(project_path.glob(marker))
                if matches:
                    self.detected_files.extend(matches)
            else:
                # Direct file check
                file_path = project_path / marker
                if file_path.exists():
                    self.detected_files.append(file_path)

        return len(self.detected_files) > 0

    def __repr__(self) -> str:
        return f"LanguagePathway({self.name}, priority={self.priority})"


# Define language pathways
PATHWAYS = [
    LanguagePathway(
        name="python",
        markers=[
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "Pipfile",
            "uv.lock",
            "poetry.lock",
        ],
        priority=100,
        description="Python development with uv, pytest, ruff",
    ),
    LanguagePathway(
        name="javascript",
        markers=[
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "tsconfig.json",
        ],
        priority=90,
        description="JavaScript/TypeScript development with npm/yarn/pnpm",
    ),
    LanguagePathway(
        name="rust",
        markers=[
            "Cargo.toml",
            "Cargo.lock",
        ],
        priority=85,
        description="Rust development with cargo",
    ),
    LanguagePathway(
        name="go",
        markers=[
            "go.mod",
            "go.sum",
        ],
        priority=80,
        description="Go development with go modules",
    ),
    LanguagePathway(
        name="java",
        markers=[
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
        ],
        priority=75,
        description="Java development with Maven/Gradle",
    ),
    LanguagePathway(
        name="csharp",
        markers=[
            "*.csproj",
            "*.sln",
            "packages.config",
        ],
        priority=70,
        description="C# development with .NET",
    ),
]


class PathwayDetector:
    """Detects and manages language pathways for a project."""

    def __init__(self, project_path: Path | str = "."):
        self.project_path = Path(project_path).resolve()
        self.detected_pathways: list[LanguagePathway] = []

    def detect_all(self) -> list[LanguagePathway]:
        """Detect all applicable language pathways."""
        self.detected_pathways = []

        for pathway in PATHWAYS:
            if pathway.detect(self.project_path):
                self.detected_pathways.append(pathway)

        # Sort by priority (highest first)
        self.detected_pathways.sort(key=lambda p: p.priority, reverse=True)

        return self.detected_pathways

    def get_primary_pathway(self) -> LanguagePathway | None:
        """Get the primary (highest priority) pathway."""
        if not self.detected_pathways:
            self.detect_all()

        return self.detected_pathways[0] if self.detected_pathways else None

    def generate_activation_command(self) -> str:
        """Generate activation command for detected pathways."""
        if not self.detected_pathways:
            return "# No language pathways detected"

        primary = self.detected_pathways[0]
        commands = [f"@activate {primary.name}"]

        # Add secondary pathways if detected
        for pathway in self.detected_pathways[1:]:
            commands.append(f"@activate {pathway.name}  # Secondary")

        return "\n".join(commands)

    def generate_report(self) -> dict:
        """Generate detailed detection report."""
        if not self.detected_pathways:
            self.detect_all()

        return {
            "project_path": str(self.project_path),
            "primary_pathway": self.detected_pathways[0].name
            if self.detected_pathways
            else None,
            "all_pathways": [
                {
                    "name": pathway.name,
                    "priority": pathway.priority,
                    "description": pathway.description,
                    "detected_files": [
                        str(f.relative_to(self.project_path))
                        for f in pathway.detected_files
                    ],
                }
                for pathway in self.detected_pathways
            ],
            "activation_command": self.generate_activation_command(),
        }

    def estimate_token_savings(self) -> int:
        """Estimate tokens saved by using pathways vs loading everything."""
        if not self.detected_pathways:
            self.detect_all()

        # Estimate: Without pathways, all language contexts loaded (~15,000 tokens)
        # With pathways: Only load what's needed (~7,000 per pathway)
        baseline_cost = len(PATHWAYS) * 7000  # All pathways loaded
        actual_cost = len(self.detected_pathways) * 7000  # Only detected pathways

        return baseline_cost - actual_cost


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect language pathways for a project"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to project directory (default: current directory)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all detected pathways (not just primary)",
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument(
        "--estimate-savings",
        action="store_true",
        help="Estimate token savings from using pathways",
    )

    args = parser.parse_args()

    detector = PathwayDetector(args.path)
    detector.detect_all()

    if args.json:
        # JSON output
        report = detector.generate_report()
        if args.estimate_savings:
            report["estimated_token_savings"] = detector.estimate_token_savings()
        print(json.dumps(report, indent=2))
    else:
        # Human-readable output
        report = detector.generate_report()

        print("🔍 Language Pathway Detection")
        print(f"📁 Project: {report['project_path']}")
        print()

        if report["primary_pathway"]:
            print(f"🎯 Primary Pathway: {report['primary_pathway']}")
            print()

            if args.all and len(report["all_pathways"]) > 1:
                print("📋 All Detected Pathways:")
                for pathway in report["all_pathways"]:
                    print(f"  • {pathway['name']} (priority {pathway['priority']})")
                    print(f"    {pathway['description']}")
                    print(f"    Detected: {', '.join(pathway['detected_files'])}")
                    print()
            else:
                pathway = report["all_pathways"][0]
                print("📦 Detected Files:")
                for file in pathway["detected_files"]:
                    print(f"  • {file}")
                print()

            print("🚀 Activation:")
            print(f"  {report['activation_command']}")
            print()

            if args.estimate_savings:
                savings = detector.estimate_token_savings()
                print(f"💰 Estimated Token Savings: ~{savings:,} tokens")
                print(f"   (vs loading all {len(PATHWAYS)} pathways)")
                print()
        else:
            print("❌ No language pathways detected")
            print()
            print("Looking for:")
            for pathway in PATHWAYS:
                print(f"  • {pathway.name}: {', '.join(pathway.markers[:3])}...")
            print()

    # Exit code: 0 if pathway detected, 1 if none detected
    sys.exit(0 if detector.get_primary_pathway() else 1)


if __name__ == "__main__":
    main()
