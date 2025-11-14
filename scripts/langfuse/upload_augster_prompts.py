#!/usr/bin/env python3
"""Upload Augster core instruction prompts to Langfuse.

Uploads The Augster's core identity and operational instructions.
These define agent behavior, heuristics, and decision-making principles.

Run with: uv run python scripts/langfuse/upload_augster_prompts.py
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages" / "tta-langfuse-integration" / "src"))

from langfuse_integration import create_prompt_from_instruction_file, get_langfuse_client


def upload_augster_instructions() -> dict[str, any]:
    """Upload Augster core instruction files.

    Returns:
        dict: Upload statistics
    """
    print("\n📤 Uploading Augster instruction prompts...")

    # Augster instruction directory
    augster_dir = Path(__file__).parent.parent.parent / "packages" / "universal-agent-context" / ".augment" / "instructions"

    instruction_files = [
        "augster-core-identity.instructions.md",
        "augster-heuristics.instructions.md",
        "augster-maxims.instructions.md",
        "augster-operational-loop.instructions.md",
    ]

    uploaded = []
    skipped = []
    failed = []

    for filename in instruction_files:
        file_path = augster_dir / filename

        if not file_path.exists():
            print(f"  ⚠️  Skipping {filename} (not found)")
            skipped.append(filename)
            continue

        try:
            # Use create_prompt_from_instruction_file helper
            result = create_prompt_from_instruction_file(
                file_path=file_path,
                additional_labels=["augster", "core", "tta-dev"],
                additional_tags=["augster", "identity", "behavior"],
            )

            if result:
                name = result.get("name", filename)
                version = result.get("version", 1)
                print(f"  ✅ Uploaded {name} (version {version})")
                uploaded.append(name)
            else:
                print(f"  ⚠️  Skipped {filename} (may already exist)")
                skipped.append(filename)

        except Exception as e:
            print(f"  ❌ Failed to upload {filename}: {e}")
            failed.append(filename)

    print("\n📊 Augster Instruction Upload Summary:")
    print(f"  ✅ Uploaded: {len(uploaded)}")
    print(f"  ⚠️  Skipped: {len(skipped)}")
    print(f"  ❌ Failed: {len(failed)}")

    if uploaded:
        print("\n  Uploaded instructions:")
        for name in uploaded:
            print(f"    - {name}")

    return {
        "uploaded": uploaded,
        "skipped": skipped,
        "failed": failed,
        "total": len(instruction_files),
    }


def upload_domain_specific() -> dict[str, any]:
    """Upload domain-specific instruction files.

    Returns:
        dict: Upload statistics
    """
    print("\n📤 Uploading domain-specific instruction prompts...")

    augster_dir = Path(__file__).parent.parent.parent / "packages" / "universal-agent-context" / ".augment" / "instructions"

    domain_files = [
        "narrative-engine.instructions.md",
        "instruction.template.md",
    ]

    uploaded = []
    skipped = []
    failed = []

    for filename in domain_files:
        file_path = augster_dir / filename

        if not file_path.exists():
            print(f"  ⚠️  Skipping {filename} (not found)")
            skipped.append(filename)
            continue

        try:
            result = create_prompt_from_instruction_file(
                file_path=file_path,
                additional_labels=["domain-specific", "tta-dev"],
                additional_tags=["template", "instruction"],
            )

            if result:
                name = result.get("name", filename)
                version = result.get("version", 1)
                print(f"  ✅ Uploaded {name} (version {version})")
                uploaded.append(name)
            else:
                print(f"  ⚠️  Skipped {filename} (may already exist)")
                skipped.append(filename)

        except Exception as e:
            print(f"  ❌ Failed to upload {filename}: {e}")
            failed.append(filename)

    print("\n📊 Domain-Specific Upload Summary:")
    print(f"  ✅ Uploaded: {len(uploaded)}")
    print(f"  ⚠️  Skipped: {len(skipped)}")
    print(f"  ❌ Failed: {len(failed)}")

    if uploaded:
        print("\n  Uploaded prompts:")
        for name in uploaded:
            print(f"    - {name}")

    return {
        "uploaded": uploaded,
        "skipped": skipped,
        "failed": failed,
        "total": len(domain_files),
    }


def main():
    """Run Augster prompt upload."""
    print("🚀 Langfuse Augster Prompt Upload")
    print("=" * 50)

    # Initialize Langfuse
    try:
        client = get_langfuse_client()
        print("✅ Langfuse initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize Langfuse: {e}")
        print("\nMake sure LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY are set.")
        return 1

    # Upload Augster instructions
    augster_result = upload_augster_instructions()

    # Upload domain-specific
    domain_result = upload_domain_specific()

    # Combined summary
    total_uploaded = len(augster_result["uploaded"]) + len(domain_result["uploaded"])
    total_skipped = len(augster_result["skipped"]) + len(domain_result["skipped"])
    total_failed = len(augster_result["failed"]) + len(domain_result["failed"])

    print("\n" + "=" * 50)
    print("✨ UPLOAD COMPLETE!")
    print("\n📊 Total Statistics:")
    print(f"  ✅ Uploaded: {total_uploaded}")
    print(f"  ⚠️  Skipped: {total_skipped}")
    print(f"  ❌ Failed: {total_failed}")

    print("\nNext steps:")
    print("  1. Visit https://cloud.langfuse.com/prompts")
    print("  2. Search for 'augster' tag to see core instructions")
    print("  3. Test Augster workflow in playground")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
