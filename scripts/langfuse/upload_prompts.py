#!/usr/bin/env python3
"""
Upload TTA.dev Prompts to Langfuse

This script uploads all instruction files and prompts from the codebase to Langfuse
for versioning, management, and usage in the Langfuse playground.

Usage:
    uv run python scripts/langfuse/upload_prompts.py
"""

import sys
from pathlib import Path

# Add packages to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root / "packages" / "tta-langfuse-integration" / "src"))

from langfuse_integration import (
    PromptManager,
    create_prompt_from_instruction_file,
    initialize_langfuse,
)


def upload_instruction_files() -> dict[str, any]:
    """
    Upload all .instructions.md files to Langfuse as prompts.

    Returns:
        Dict with upload statistics
    """
    manager = PromptManager()
    instruction_dir = project_root / ".github" / "instructions"

    if not instruction_dir.exists():
        print(f"⚠️  Instruction directory not found: {instruction_dir}")
        return {"uploaded": 0, "failed": 0, "total": 0}

    instruction_files = list(instruction_dir.glob("*.instructions.md"))

    print(f"\n📋 Found {len(instruction_files)} instruction files")
    print("=" * 60)

    uploaded = 0
    failed = 0

    for file_path in instruction_files:
        try:
            # Extract metadata from file path
            file_name = file_path.stem  # e.g., "testing.instructions"
            prompt_name = file_name.replace(".instructions", "").replace("-", "_")

            # Read file to extract frontmatter
            content = file_path.read_text()

            # Parse YAML frontmatter
            apply_to = "**/*.py"
            description = f"Instructions for {prompt_name}"

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml

                    frontmatter = yaml.safe_load(parts[1])
                    apply_to = frontmatter.get("applyTo", apply_to)
                    description = frontmatter.get("description", description)

            print(f"\n📤 Uploading: {file_name}")
            print(f"   Name: {prompt_name}")
            print(f"   ApplyTo: {apply_to}")

            result = create_prompt_from_instruction_file(
                instruction_file_path=str(file_path),
                name=prompt_name,
                apply_to_pattern=apply_to,
                description=description,
                labels=["instruction", "tta-dev"],
                tags=["production", "standards"],
            )

            if result.get("disabled"):
                print(f"   ⚠️  Langfuse disabled, skipped")
            else:
                print(f"   ✅ Version: {result.get('version', 'N/A')}")
                uploaded += 1

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1

    return {
        "uploaded": uploaded,
        "failed": failed,
        "total": len(instruction_files),
    }


def upload_prompt_templates() -> dict[str, any]:
    """
    Upload prompt templates from local/.prompts directory.

    Returns:
        Dict with upload statistics
    """
    manager = PromptManager()
    prompts_dir = project_root / "local" / ".prompts"

    if not prompts_dir.exists():
        print(f"⚠️  Prompts directory not found: {prompts_dir}")
        return {"uploaded": 0, "failed": 0, "total": 0}

    prompt_files = list(prompts_dir.glob("*.md"))
    # Exclude README and templates
    prompt_files = [f for f in prompt_files if f.name.lower() != "readme.md"]

    print(f"\n📝 Found {len(prompt_files)} prompt files")
    print("=" * 60)

    uploaded = 0
    failed = 0

    for file_path in prompt_files:
        try:
            prompt_name = file_path.stem.replace("-", "_")

            print(f"\n📤 Uploading: {file_path.name}")
            print(f"   Name: {prompt_name}")

            content = file_path.read_text()

            # Extract metadata from markdown headers
            description = "Custom prompt"
            if "**Version:**" in content:
                # Extract version line
                for line in content.split("\n"):
                    if "**Version:**" in line:
                        description = line.split("**Version:**")[1].strip()
                        break

            result = manager.create_prompt(
                name=prompt_name,
                prompt=content,
                config={"source": "local/.prompts", "type": "agent-mode"},
                labels=["prompt", "agent"],
                tags=["production", "tta-dev"],
            )

            if result.get("disabled"):
                print(f"   ⚠️  Langfuse disabled, skipped")
            else:
                print(f"   ✅ Version: {result.get('version', 'N/A')}")
                uploaded += 1

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1

    return {
        "uploaded": uploaded,
        "failed": failed,
        "total": len(prompt_files),
    }


def upload_system_prompts() -> dict[str, any]:
    """
    Upload common system prompts found in scripts and tests.

    Returns:
        Dict with upload statistics
    """
    manager = PromptManager()

    print(f"\n🤖 Uploading system prompts")
    print("=" * 60)

    system_prompts = [
        {
            "name": "structured_data_assistant",
            "prompt": "You are a structured data assistant. Respond with valid JSON only.",
            "config": {"use_case": "json-generation", "temperature": 0.3},
            "labels": ["system-prompt"],
            "tags": ["json", "structured-output"],
        },
        {
            "name": "tool_selection_agent",
            "prompt": """You are a tool selection agent. Available tools:
- search(query: str) - Search for information
- calculator(expression: str) - Perform calculations
- file_reader(path: str) - Read file contents

When you need to use a tool, respond with: TOOL: tool_name(arguments)""",
            "config": {"use_case": "tool-use", "temperature": 0.5},
            "labels": ["system-prompt"],
            "tags": ["tools", "agent"],
        },
        {
            "name": "code_quality_reviewer",
            "prompt": "You are an expert code reviewer. Analyze code for quality, best practices, security, and maintainability. Provide specific, actionable feedback.",
            "config": {"use_case": "code-review", "temperature": 0.4},
            "labels": ["system-prompt"],
            "tags": ["code-review", "quality"],
        },
        {
            "name": "test_generator",
            "prompt": "You are a test generation expert. Create comprehensive pytest tests with fixtures, mocks, and edge cases. Follow AAA pattern (Arrange, Act, Assert).",
            "config": {"use_case": "test-generation", "temperature": 0.3},
            "labels": ["system-prompt"],
            "tags": ["testing", "pytest"],
        },
        {
            "name": "documentation_writer",
            "prompt": "You are a technical documentation expert. Write clear, comprehensive documentation with examples, parameters, and return types. Use markdown formatting.",
            "config": {"use_case": "documentation", "temperature": 0.4},
            "labels": ["system-prompt"],
            "tags": ["documentation", "markdown"],
        },
    ]

    uploaded = 0
    failed = 0

    for prompt_data in system_prompts:
        try:
            print(f"\n📤 Uploading: {prompt_data['name']}")

            result = manager.create_prompt(**prompt_data)

            if result.get("disabled"):
                print(f"   ⚠️  Langfuse disabled, skipped")
            else:
                print(f"   ✅ Version: {result.get('version', 'N/A')}")
                uploaded += 1

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1

    return {
        "uploaded": uploaded,
        "failed": failed,
        "total": len(system_prompts),
    }


def main():
    """Main execution function."""
    print("\n" + "=" * 60)
    print("🚀 TTA.dev Langfuse Prompt Library Upload")
    print("=" * 60)

    # Initialize Langfuse (uses environment variables)
    try:
        initialize_langfuse()
        print("✅ Langfuse initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Langfuse: {e}")
        print("\nMake sure LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set!")
        sys.exit(1)

    # Upload all prompts
    results = {
        "instructions": upload_instruction_files(),
        "prompts": upload_prompt_templates(),
        "system": upload_system_prompts(),
    }

    # Print summary
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)

    total_uploaded = 0
    total_failed = 0
    total_all = 0

    for category, stats in results.items():
        print(f"\n{category.title()}:")
        print(f"  ✅ Uploaded: {stats['uploaded']}/{stats['total']}")
        if stats['failed'] > 0:
            print(f"  ❌ Failed: {stats['failed']}")

        total_uploaded += stats['uploaded']
        total_failed += stats['failed']
        total_all += stats['total']

    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total_uploaded}/{total_all} prompts uploaded")
    if total_failed > 0:
        print(f"❌ {total_failed} failed")
    print(f"{'=' * 60}\n")

    print("🎉 All prompts uploaded to Langfuse!")
    print("📊 View them at: https://cloud.langfuse.com/prompts")


if __name__ == "__main__":
    main()
