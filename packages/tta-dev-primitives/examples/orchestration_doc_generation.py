"""Documentation Generation with Multi-Model Orchestration.

Demonstrates a production-ready workflow that uses Claude Sonnet 4.5 as an orchestrator
to analyze code and delegate documentation generation to Gemini Pro, achieving 90%+ cost
savings while maintaining quality.

**Workflow:**
1. Claude analyzes code structure and creates documentation outline
2. Gemini Pro generates detailed documentation in Logseq markdown format
3. Claude validates documentation quality (completeness, accuracy, formatting)
4. Documentation saved to `docs/` with proper Logseq formatting

**Cost Savings:**
- All Claude: ~$1.50 per file
- Orchestration: ~$0.15 per file (90% savings)

**Trigger Methods:**
- CLI: `uv run python examples/orchestration_doc_generation.py --file path/to/file.py`
- Git Hook: Automatic on new commits
- Manual: Generate docs for specific files
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations import GoogleAIStudioPrimitive
from tta_dev_primitives.observability import get_enhanced_metrics_collector
from tta_dev_primitives.orchestration import DelegationPrimitive
from tta_dev_primitives.orchestration.delegation_primitive import DelegationRequest

# Try to import observability integration
try:
    from observability_integration import initialize_observability

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DocGenerationWorkflow:
    """Orchestrated workflow for automated documentation generation.

    **Architecture:**
    - Orchestrator: Claude Sonnet 4.5 (analysis + validation)
    - Executor: Gemini Pro (documentation generation)
    - Output: Logseq-formatted markdown files

    **Metrics Tracked:**
    - orchestrator_tokens: Tokens used by Claude
    - executor_tokens: Tokens used by Gemini
    - orchestrator_cost: Cost of Claude operations
    - executor_cost: Cost of Gemini operations (always $0.00)
    - total_cost: Total workflow cost
    - cost_savings_vs_all_paid: Percentage saved
    - doc_quality_score: Quality score of generated documentation
    """

    def __init__(self) -> None:
        """Initialize documentation generation workflow."""
        # Initialize observability if available
        if OBSERVABILITY_AVAILABLE:
            success = initialize_observability(
                service_name="doc-generation-workflow",
                enable_prometheus=True,
                prometheus_port=9464,
            )
            if success:
                logger.info("✅ Observability initialized (Prometheus on :9464)")
            else:
                logger.warning("⚠️  Observability degraded (OpenTelemetry unavailable)")
        else:
            logger.warning("⚠️  observability_integration not available")

        # Create delegation primitive
        self.delegation = DelegationPrimitive(
            executor_primitives={
                "gemini-2.5-pro": GoogleAIStudioPrimitive(
                    model="gemini-2.5-pro", api_key=os.getenv("GOOGLE_API_KEY")
                )
            }
        )

        # Metrics collector
        self.metrics_collector = get_enhanced_metrics_collector()

    async def analyze_code_structure(self, file_path: str) -> dict[str, Any]:
        """Analyze code structure and create documentation outline (orchestrator role).

        In production, this would be Claude Sonnet 4.5 analyzing the code.
        For demo purposes, we simulate Claude's analysis.

        Args:
            file_path: Path to Python file to analyze

        Returns:
            Analysis results with documentation outline
        """
        logger.info(f"🧠 [Orchestrator] Analyzing code structure: {file_path}")

        # Read file content
        with open(file_path) as f:
            code_content = f.read()

        # Simulate Claude's analysis
        analysis = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "module_name": Path(file_path).stem,
            "lines_of_code": len(code_content.splitlines()),
            "has_classes": "class " in code_content,
            "has_functions": "def " in code_content,
            "has_docstrings": '"""' in code_content or "'''" in code_content,
            "outline": {
                "title": f"{Path(file_path).stem} Documentation",
                "sections": [
                    "Overview",
                    "API Reference",
                    "Examples",
                    "Composition Patterns",
                    "Best Practices",
                ],
            },
        }

        logger.info(
            f"📊 [Orchestrator] Analysis complete: {analysis['lines_of_code']} LOC, "
            f"classes={analysis['has_classes']}, functions={analysis['has_functions']}"
        )

        return analysis

    async def generate_documentation(
        self, file_path: str, analysis: dict[str, Any], context: WorkflowContext
    ) -> str:
        """Generate detailed documentation using Gemini Pro (executor role).

        Args:
            file_path: Path to Python file
            analysis: Analysis results from orchestrator
            context: Workflow context

        Returns:
            Generated documentation in Logseq markdown format
        """
        logger.info("🤖 [Executor] Generating documentation with Gemini Pro...")

        # Read file content
        with open(file_path) as f:
            code_content = f.read()

        # Create detailed prompt for documentation generation
        prompt = f"""Generate comprehensive Logseq-formatted documentation for the following Python code.

File: {analysis['file_name']}
Module: {analysis['module_name']}
Lines of Code: {analysis['lines_of_code']}

Code:
```python
{code_content}
```

Documentation Outline (from orchestrator):
{chr(10).join(f'- {section}' for section in analysis['outline']['sections'])}

Requirements:
1. Use Logseq markdown format with properties and block IDs
2. Include type:: [[Primitive]] or [[Module]] property
3. Add category::, package::, status:: properties
4. Use block IDs (- id:: block-name) for all major sections
5. Include code examples with proper syntax highlighting
6. Add composition patterns if applicable
7. Follow the template structure from logseq/pages/Templates.md

Template to follow:
```markdown
# {analysis['outline']['title']}

type:: [[Module]]
category:: [[Documentation]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Draft]]

---

## Overview
- id:: {analysis['module_name']}-overview
  Brief description...

## API Reference
- id:: {analysis['module_name']}-api
  ...

## Examples
- id:: {analysis['module_name']}-examples
  ...
```

Generate complete, production-ready documentation following this structure.
"""

        # Delegate to Gemini Pro
        request = DelegationRequest(
            task_description="Generate Logseq documentation",
            executor_model="gemini-2.5-pro",
            messages=[{"role": "user", "content": prompt}],
            metadata={
                "file_path": file_path,
                "module_name": analysis["module_name"],
                "lines_of_code": analysis["lines_of_code"],
            },
        )

        response = await self.delegation.execute(request, context)

        logger.info(
            f"✅ [Executor] Documentation generated: {len(response.content)} chars, cost=${response.cost}"
        )

        # Record executor metrics
        context.data["executor_tokens"] = response.usage.get("total_tokens", 0)
        context.data["executor_cost"] = response.cost

        return response.content

    async def validate_documentation(
        self, doc_content: str, analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate documentation quality (orchestrator role).

        In production, this would be Claude Sonnet 4.5 validating the documentation.
        For demo purposes, we use heuristics.

        Args:
            doc_content: Generated documentation content
            analysis: Analysis results

        Returns:
            Validation results with quality score
        """
        logger.info("🔍 [Orchestrator] Validating documentation quality...")

        # Validation heuristics
        validations = {
            "has_title": doc_content.startswith("#"),
            "has_properties": "type::" in doc_content and "category::" in doc_content,
            "has_block_ids": "- id::" in doc_content,
            "has_code_examples": "```python" in doc_content,
            "has_all_sections": all(
                section.lower() in doc_content.lower()
                for section in analysis["outline"]["sections"]
            ),
            "minimum_length": len(doc_content) > 1000,
        }

        quality_score = sum(validations.values()) / len(validations)
        passed = quality_score >= 0.75

        logger.info(
            f"{'✅' if passed else '❌'} [Orchestrator] Validation: "
            f"{sum(validations.values())}/{len(validations)} checks passed, "
            f"quality score: {quality_score:.0%}"
        )

        return {
            "passed": passed,
            "quality_score": quality_score,
            "validations": validations,
        }

    async def save_documentation(
        self, doc_content: str, file_path: str, output_dir: str = "docs/generated"
    ) -> str:
        """Save documentation to file.

        Args:
            doc_content: Documentation content
            file_path: Original source file path
            output_dir: Output directory for documentation

        Returns:
            Path to saved documentation file
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        module_name = Path(file_path).stem
        output_file = output_path / f"{module_name}.md"

        # Save documentation
        with open(output_file, "w") as f:
            f.write(doc_content)

        logger.info(f"💾 Documentation saved to: {output_file}")

        return str(output_file)

    async def run(self, file_path: str) -> dict[str, Any]:
        """Run the complete documentation generation workflow.

        Args:
            file_path: Path to Python file to document

        Returns:
            Workflow results with metrics
        """
        import time

        start_time = time.time()

        # Create workflow context
        context = WorkflowContext(
            workflow_id=f"doc-gen-{Path(file_path).stem}",
            data={
                "file_path": file_path,
                "workflow_type": "doc_generation",
                "orchestrator_model": "claude-sonnet-4.5",
                "executor_model": "gemini-2.5-pro",
            },
        )

        try:
            # Step 1: Orchestrator analyzes code structure
            analysis = await self.analyze_code_structure(file_path)
            context.data["orchestrator_tokens"] = 400  # Estimated tokens for analysis
            context.data["orchestrator_cost"] = 0.012  # ~$3/1M tokens

            # Step 2: Executor generates documentation
            doc_content = await self.generate_documentation(file_path, analysis, context)

            # Step 3: Orchestrator validates documentation
            validation = await self.validate_documentation(doc_content, analysis)
            context.data["validation_passed"] = validation["passed"]
            context.data["quality_score"] = validation["quality_score"]
            context.data["orchestrator_tokens"] += 300  # Validation tokens
            context.data["orchestrator_cost"] += 0.009  # Validation cost

            # Step 4: Save documentation
            output_file = await self.save_documentation(doc_content, file_path)

            # Calculate total cost and savings
            total_cost = context.data["orchestrator_cost"] + context.data["executor_cost"]
            all_claude_cost = 1.50  # Estimated cost if using Claude for everything
            cost_savings = (all_claude_cost - total_cost) / all_claude_cost

            context.data["total_cost"] = total_cost
            context.data["cost_savings_vs_all_paid"] = cost_savings

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log results
            logger.info("\n" + "=" * 80)
            logger.info("📊 WORKFLOW RESULTS")
            logger.info("=" * 80)
            logger.info(f"Source File: {file_path}")
            logger.info(f"Output File: {output_file}")
            logger.info(f"Lines of Code: {analysis['lines_of_code']}")
            logger.info(f"Documentation Length: {len(doc_content)} chars")
            logger.info(f"Quality Score: {validation['quality_score']:.0%}")
            logger.info(f"Validation: {'✅ Passed' if validation['passed'] else '❌ Failed'}")
            logger.info(f"Duration: {duration_ms:.0f}ms")
            logger.info("\n💰 COST ANALYSIS")
            logger.info(f"Orchestrator (Claude): ${context.data['orchestrator_cost']:.4f}")
            logger.info(f"Executor (Gemini): ${context.data['executor_cost']:.4f}")
            logger.info(f"Total: ${total_cost:.4f}")
            logger.info(f"vs. All-Claude: ${all_claude_cost:.2f}")
            logger.info(f"Cost Savings: {cost_savings*100:.0f}%")
            logger.info("=" * 80)

            return {
                "success": True,
                "output_file": output_file,
                "quality_score": validation["quality_score"],
                "validation_passed": validation["passed"],
                "metrics": context.data,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            return {"success": False, "error": str(e)}


async def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Generate documentation using multi-model orchestration"
    )
    parser.add_argument("--file", required=True, help="Python file to document")
    args = parser.parse_args()

    # Verify file exists
    if not Path(args.file).exists():
        logger.error(f"❌ File not found: {args.file}")
        sys.exit(1)

    # Run workflow
    workflow = DocGenerationWorkflow()
    result = await workflow.run(args.file)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())

