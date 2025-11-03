#!/usr/bin/env python3
"""CLI tool for updating the LLM Cost Guide.

This script uses FreeTierResearchPrimitive to automatically research
current free tier information and update the guide.

Usage:
    uv run python scripts/update-free-tiers.py
    uv run python scripts/update-free-tiers.py --providers openai anthropic
    uv run python scripts/update-free-tiers.py --output custom-guide.md
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "tta-dev-primitives" / "src"))

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.research import (
    FreeTierResearchPrimitive,
    FreeTierResearchRequest,
)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Update the LLM Cost Guide with current provider information"
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=["openai", "anthropic", "google-gemini", "openrouter", "ollama"],
        help="Providers to research (default: all)",
    )
    parser.add_argument(
        "--existing-guide",
        default="docs/guides/llm-cost-guide.md",
        help="Path to existing guide for comparison",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write updated guide (default: print to stdout)",
    )
    parser.add_argument(
        "--no-changelog",
        action="store_true",
        help="Disable changelog generation",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output",
    )
    parser.add_argument(
        "--include-quality-rankings",
        action="store_true",
        help="Include best free models ranking in output",
    )
    parser.add_argument(
        "--generate-fallback-strategy",
        type=str,
        metavar="USE_CASE",
        help="Generate fallback strategy for use case (e.g., 'code-generation', 'reasoning')",
    )

    args = parser.parse_args()

    # Create primitive and context
    primitive = FreeTierResearchPrimitive()
    context = WorkflowContext(workflow_id="cli-update-free-tiers")

    # Create request
    request = FreeTierResearchRequest(
        providers=args.providers,
        existing_guide_path=args.existing_guide if not args.no_changelog else None,
        output_path=args.output,
        generate_changelog=not args.no_changelog,
    )

    if not args.quiet:
        print(f"🔍 Researching {len(args.providers)} providers...")
        print(f"   Providers: {', '.join(args.providers)}")

    # Execute research
    response = await primitive.execute(request, context)

    if not args.quiet:
        print(f"✅ Research complete ({response.research_date})")
        print()

    # Display results
    if response.changelog and not args.quiet:
        print("📝 Changelog:")
        for change in response.changelog:
            print(f"   - {change}")
        print()

    # Display provider summary
    if not args.quiet:
        print("📊 Provider Summary:")
        for provider_name, info in response.providers.items():
            free_status = "✅ Free" if info.has_free_tier else "❌ Paid"
            print(f"   {info.name}: {free_status}")
            if info.free_tier_details:
                print(f"      └─ {info.free_tier_details}")
        print()

    # Display quality rankings if requested
    if args.include_quality_rankings:
        print("🏆 Best Free Models (Ranked):")
        print("=" * 80)
        ranked_models = primitive.generate_best_free_models_ranking(response.providers)

        # Print header
        print(f"{'Rank':<6} {'Model':<35} {'Provider':<20} {'Score':<8} {'Best For'}")
        print("-" * 80)

        # Print top 10 models
        for rank, model, provider in ranked_models[:10]:
            best_for = ", ".join(model.best_for[:2])  # Show first 2 use cases
            print(
                f"{rank:<6} {model.model_name:<35} {provider.name:<20} "
                f"{model.overall_score:<8.1f} {best_for}"
            )
        print("=" * 80)
        print()

    # Generate fallback strategy if requested
    if args.generate_fallback_strategy:
        print(f"🎯 Recommended Fallback Strategy for: {args.generate_fallback_strategy}")
        print("=" * 80)
        strategy_code = primitive.generate_fallback_strategy(
            args.generate_fallback_strategy, response.providers
        )
        print(strategy_code)
        print("=" * 80)
        print()

    # Output guide
    if response.updated_guide:
        if args.output:
            # Write to file
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(response.updated_guide)
            if not args.quiet:
                print(f"💾 Guide written to: {args.output}")
        else:
            # Print to stdout
            print("📄 Generated Guide:")
            print("=" * 80)
            print(response.updated_guide)
            print("=" * 80)

    if not args.quiet:
        print()
        print("✨ Done!")


if __name__ == "__main__":
    asyncio.run(main())
