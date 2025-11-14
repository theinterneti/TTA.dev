#!/usr/bin/env python3
"""Upload workflow prompts to Langfuse.

Uploads agentic workflow prompts from .augment/workflows/ directory.
These are production-ready workflows for systematic development tasks.

Run with: uv run python scripts/langfuse/upload_workflow_prompts.py
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "tta-langfuse-integration" / "src"))

from langfuse_integration import PromptManager, get_langfuse_client


def upload_workflow_prompts() -> dict[str, any]:
    """Upload all workflow prompts from .augment/workflows/ directory.

    Returns:
        dict: Upload statistics
    """
    print("\n📤 Uploading workflow prompts...")

    manager = PromptManager()

    # Workflow prompt files
    workflow_dir = Path(__file__).parent.parent.parent / "packages" / "universal-agent-context" / ".augment" / "workflows"

    workflow_files = [
        "augster-axiomatic-workflow.prompt.md",
        "feature-implementation.prompt.md",
        "bug-fix.prompt.md",
        "component-promotion.prompt.md",
        "quality-gate-fix.prompt.md",
        "test-coverage-improvement.prompt.md",
    ]

    uploaded = []
    skipped = []
    failed = []

    for filename in workflow_files:
        file_path = workflow_dir / filename

        if not file_path.exists():
            print(f"  ⚠️  Skipping {filename} (not found)")
            skipped.append(filename)
            continue

        try:
            # Read file content
            content = file_path.read_text()

            # Extract YAML frontmatter if present
            metadata = {}
            if content.startswith("# "):
                # Extract title from first header
                first_line = content.split("\n")[0]
                title = first_line.replace("# ", "").strip()

                # Try to find Purpose or Description
                for line in content.split("\n")[1:10]:
                    if line.startswith("**Purpose:**"):
                        purpose = line.replace("**Purpose:**", "").strip()
                        metadata["description"] = purpose
                        break

            # Generate prompt name from filename
            prompt_name = filename.replace(".prompt.md", "").replace("-", "_")

            # Create prompt
            result = manager.create_prompt(
                name=prompt_name,
                prompt=content,
                labels=["workflow", "agentic", "tta-dev"],
                tags=["workflow", "production", "systematic"],
                config={
                    "type": "workflow",
                    "source": str(file_path.relative_to(Path.cwd())),
                    "category": "agentic-workflow",
                },
            )

            if result:
                version = result.get("version", 1)
                print(f"  ✅ Uploaded {prompt_name} (version {version})")
                uploaded.append(prompt_name)
            else:
                print(f"  ⚠️  Skipped {prompt_name} (may already exist)")
                skipped.append(prompt_name)

        except Exception as e:
            print(f"  ❌ Failed to upload {filename}: {e}")
            failed.append(filename)

    print("\n📊 Workflow Upload Summary:")
    print(f"  ✅ Uploaded: {len(uploaded)}")
    print(f"  ⚠️  Skipped: {len(skipped)}")
    print(f"  ❌ Failed: {len(failed)}")

    if uploaded:
        print("\n  Uploaded workflows:")
        for name in uploaded:
            print(f"    - {name}")

    return {
        "uploaded": uploaded,
        "skipped": skipped,
        "failed": failed,
        "total": len(workflow_files),
    }


def main():
    """Run workflow prompt upload."""
    print("🚀 Langfuse Workflow Prompt Upload")
    print("=" * 50)

    # Initialize Langfuse
    try:
        client = get_langfuse_client()
        print("✅ Langfuse initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize Langfuse: {e}")
        print("\nMake sure LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY are set.")
        return 1

    # Upload workflow prompts
    result = upload_workflow_prompts()

    # Summary
    print("\n" + "=" * 50)
    print("✨ UPLOAD COMPLETE!")
    print(f"\nUploaded {result['uploaded'].__len__()} workflow prompts to Langfuse")
    print("\nNext steps:")
    print("  1. Visit https://cloud.langfuse.com/prompts")
    print("  2. Test workflows in playground")
    print("  3. Run evaluators on workflow outputs")

    return 0 if not result["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
