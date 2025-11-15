"""
Enhanced Skills Management with Logseq and ACE Integration

Combines MCP Code Execution with persistent Logseq storage and ACE learning patterns
for cross-session agent skill development and improvement tracking.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from tta_dev_primitives.ace import (
    ACEInput,
    SelfLearningCodePrimitive,
)
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.integrations.mcp_code_execution_primitive import (
    MCPCodeExecutionPrimitive,
)
from tta_dev_primitives.knowledge.knowledge_base import (
    KBQuery,
    KnowledgeBasePrimitive,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogseqSkillsIntegration:
    """Persist skills data to Logseq knowledge base."""

    def __init__(self, logseq_path: str = "./logseq"):
        """Initialize with Logseq directory path."""
        self.logseq_path = Path(logseq_path)
        self.skills_page_path = (
            self.logseq_path / "pages" / "Agent Skills Development.md"
        )
        self.journals_path = self.logseq_path / "journals"

    async def save_skill_progress(
        self, skill_name: str, skill_data: dict, context: str = ""
    ):
        """Save skill progress to Logseq pages and daily journal."""
        # Ensure directories exist
        self.skills_page_path.parent.mkdir(parents=True, exist_ok=True)
        self.journals_path.mkdir(parents=True, exist_ok=True)

        # Update main skills page
        await self._update_skills_page(skill_name, skill_data, context)

        # Log to today's journal
        await self._log_to_journal(skill_name, skill_data, context)

    async def _update_skills_page(
        self, skill_name: str, skill_data: dict, context: str
    ):
        """Update the main agent skills page."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create or update skills page
        skills_content = f"""# Agent Skills Development

## {skill_name}

**Last Updated:** {timestamp}
**Context:** {context}
**Success Rate:** {skill_data.get("success_rate", 0):.1%}
**Total Attempts:** {skill_data.get("attempts", 0)}
**Proficiency Level:** {skill_data.get("proficiency", "novice")}

### Learning History

```json
{json.dumps(skill_data, indent=2)}
```

### Related Skills

{{{{query (and [[Agent Skills]] [[{skill_name}]])}}}}

### Improvement Strategies

- Track execution patterns and failure modes
- Integrate with ACE framework for continuous learning
- Use MCP code execution for safe skill practice
- Maintain cross-session persistence via Logseq

"""

        # Write to file
        with open(self.skills_page_path, "w", encoding="utf-8") as f:
            f.write(skills_content)

        logger.info(f"Updated Logseq skills page for {skill_name}")

    async def _log_to_journal(self, skill_name: str, skill_data: dict, context: str):
        """Log skill update to today's journal."""
        today = datetime.now().strftime("%Y_%m_%d")
        journal_path = self.journals_path / f"{today}.md"

        timestamp = datetime.now().strftime("%H:%M:%S")
        journal_entry = f"""
## {timestamp} - Agent Skills Update

- UPDATED [[Agent Skills Development]] - [[{skill_name}]] #agent-skills
  success-rate:: {skill_data.get("success_rate", 0):.1%}
  attempts:: {skill_data.get("attempts", 0)}
  context:: {context}
  proficiency:: {skill_data.get("proficiency", "novice")}

"""

        # Append to journal
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(journal_entry)

        logger.info(f"Logged skills update to journal: {today}")


class EnhancedSkillsPrimitive:
    """Enhanced skills management with MCP, Logseq, and ACE integration."""

    def __init__(self, e2b_api_key: str | None = None, logseq_path: str = "./logseq"):
        """Initialize enhanced skills primitive."""
        self.mcp_primitive = MCPCodeExecutionPrimitive(
            api_key=e2b_api_key, default_timeout=120, workspace_dir="./workspace"
        )
        self.knowledge_base = KnowledgeBasePrimitive()
        self.ace_learner = SelfLearningCodePrimitive()
        self.logseq_integration = LogseqSkillsIntegration(logseq_path)

        # In-memory skills cache
        self.skills_cache = {}

    async def develop_skill(
        self,
        skill_name: str,
        task_description: str,
        context: WorkflowContext,
        learning_context: str = "",
    ) -> dict[str, Any]:
        """Develop a skill using MCP execution, ACE learning, and Logseq persistence."""

        # Step 1: Query Logseq for existing knowledge
        kb_query = KBQuery(
            query_type="best_practices",
            topic=skill_name,
            tags=["agent-skills", "learning"],
            max_results=3,
        )

        try:
            kb_result = await self.knowledge_base.execute(kb_query, context)
            existing_knowledge = kb_result.pages
        except Exception as e:
            logger.warning(f"Could not query knowledge base: {e}")
            existing_knowledge = []

        # Step 2: Use ACE framework for intelligent code generation
        ace_input = ACEInput(
            task=f"Develop skill: {skill_name} - {task_description}",
            language="python",
            context=f"Learning context: {learning_context}",
            previous_attempts=self.skills_cache.get(skill_name, {}).get(
                "previous_code", []
            ),
        )

        try:
            ace_result = await self.ace_learner.execute(ace_input, context)
            generated_code = ace_result.code_generated
            ace_strategies = ace_result.strategies_learned
        except Exception as e:
            logger.warning(f"ACE learning failed, using fallback: {e}")
            generated_code = self._generate_fallback_skill_code(
                skill_name, task_description
            )
            ace_strategies = []

        # Step 3: Execute skill practice in MCP sandbox
        skill_practice_code = f"""
# Skill Development: {skill_name}
# Task: {task_description}
# Context: {learning_context}

import json
from datetime import datetime

class SkillTracker:
    def __init__(self, skill_name):
        self.skill_name = skill_name
        self.attempts = []
        self.success_count = 0

    def practice_skill(self):
        \"\"\"Practice the specific skill.\"\"\"
        try:
            # Generated skill code
{self._indent_code(generated_code, 12)}

            return True, "Skill practice successful"
        except Exception as e:
            return False, f"Skill practice failed: {{e}}"

    def record_attempt(self, success, details):
        attempt = {{
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "details": details
        }}
        self.attempts.append(attempt)
        if success:
            self.success_count += 1

    def get_skill_metrics(self):
        total_attempts = len(self.attempts)
        success_rate = self.success_count / total_attempts if total_attempts > 0 else 0

        proficiency = "expert" if success_rate > 0.8 else \
                     "intermediate" if success_rate > 0.6 else "novice"

        return {{
            "skill_name": self.skill_name,
            "success_rate": success_rate,
            "attempts": total_attempts,
            "proficiency": proficiency,
            "recent_attempts": self.attempts[-5:],  # Last 5 attempts
            "improvement_trend": self._calculate_trend()
        }}

    def _calculate_trend(self):
        if len(self.attempts) < 2:
            return "insufficient_data"

        recent_success = sum(1 for a in self.attempts[-5:] if a["success"])
        earlier_success = sum(1 for a in self.attempts[-10:-5] if a["success"]) if len(self.attempts) >= 10 else 0

        if recent_success > earlier_success:
            return "improving"
        elif recent_success < earlier_success:
            return "declining"
        else:
            return "stable"

# Practice the skill
tracker = SkillTracker("{skill_name}")
success, details = tracker.practice_skill()
tracker.record_attempt(success, details)

# Get metrics
metrics = tracker.get_skill_metrics()
print(f"Skill development result: {{metrics}}")

metrics
"""

        # Execute in MCP sandbox
        try:
            mcp_result = await self.mcp_primitive.execute(
                {
                    "code": skill_practice_code,
                    "workspace_data": {
                        "skill_name": skill_name,
                        "learning_context": learning_context,
                    },
                },
                context,
            )

            skill_metrics = mcp_result.get("result", {})
            execution_success = True

        except Exception as e:
            logger.error(f"MCP execution failed: {e}")
            skill_metrics = {
                "skill_name": skill_name,
                "success_rate": 0.0,
                "attempts": 1,
                "proficiency": "novice",
                "error": str(e),
            }
            execution_success = False

        # Step 4: Update skills cache
        self.skills_cache[skill_name] = {
            "metrics": skill_metrics,
            "previous_code": self.skills_cache.get(skill_name, {}).get(
                "previous_code", []
            )
            + [generated_code],
            "last_updated": datetime.now().isoformat(),
        }

        # Step 5: Persist to Logseq
        try:
            await self.logseq_integration.save_skill_progress(
                skill_name=skill_name,
                skill_data=skill_metrics,
                context=learning_context,
            )
            logseq_success = True
        except Exception as e:
            logger.error(f"Logseq persistence failed: {e}")
            logseq_success = False

        return {
            "skill_name": skill_name,
            "task_description": task_description,
            "learning_context": learning_context,
            "skill_metrics": skill_metrics,
            "ace_strategies_learned": len(ace_strategies),
            "existing_knowledge_found": len(existing_knowledge),
            "execution_success": execution_success,
            "logseq_persistence": logseq_success,
            "generated_code_preview": generated_code[:200] + "..."
            if len(generated_code) > 200
            else generated_code,
            "integration_status": {
                "mcp_execution": "success" if execution_success else "failed",
                "ace_learning": "success" if ace_strategies else "fallback",
                "logseq_storage": "success" if logseq_success else "failed",
                "knowledge_base": "success" if existing_knowledge else "empty",
            },
        }

    def _generate_fallback_skill_code(
        self, skill_name: str, task_description: str
    ) -> str:
        """Generate fallback skill code when ACE fails."""
        return f"""
# Fallback skill implementation for: {skill_name}
def practice_{skill_name.lower().replace(" ", "_")}():
    \"\"\"Practice {skill_name}: {task_description}\"\"\"
    print(f"Practicing skill: {skill_name}")
    print(f"Task: {task_description}")

    # Basic skill practice logic
    result = "skill_practice_completed"
    return result

# Execute skill practice
result = practice_{skill_name.lower().replace(" ", "_")}()
print(f"Skill practice result: {{result}}")
"""

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces."""
        indent = " " * spaces
        return "\n".join(indent + line for line in code.split("\n"))

    async def get_skill_summary(self, context: WorkflowContext) -> dict[str, Any]:
        """Get summary of all developed skills."""
        return {
            "total_skills": len(self.skills_cache),
            "skills_overview": {
                name: {
                    "proficiency": data["metrics"].get("proficiency", "unknown"),
                    "success_rate": data["metrics"].get("success_rate", 0),
                    "last_updated": data.get("last_updated", "unknown"),
                }
                for name, data in self.skills_cache.items()
            },
            "expert_skills": [
                name
                for name, data in self.skills_cache.items()
                if data["metrics"].get("proficiency") == "expert"
            ],
            "cache_size": len(self.skills_cache),
        }


async def demonstrate_enhanced_skills():
    """Demonstrate the enhanced skills management system."""
    print("🧠 Enhanced Skills Management - MCP + Logseq + ACE Integration")
    print("=" * 70)

    # Initialize system
    skills_primitive = EnhancedSkillsPrimitive(
        e2b_api_key="demo-key",  # Works in demo mode
        logseq_path="./logseq",
    )

    context = WorkflowContext(trace_id="enhanced-skills-demo")

    # Develop multiple skills
    skills_to_develop = [
        (
            "Data Analysis",
            "Analyze error patterns in log files",
            "Production debugging",
        ),
        (
            "API Integration",
            "Connect to external services reliably",
            "Service integration",
        ),
        (
            "Code Generation",
            "Generate Python functions from specifications",
            "Development automation",
        ),
    ]

    results = []

    for skill_name, task_desc, learning_context in skills_to_develop:
        print(f"\n🎯 Developing Skill: {skill_name}")
        print(f"Task: {task_desc}")
        print(f"Context: {learning_context}")

        result = await skills_primitive.develop_skill(
            skill_name=skill_name,
            task_description=task_desc,
            context=context,
            learning_context=learning_context,
        )

        results.append(result)

        # Show integration status
        integration = result["integration_status"]
        print(f"✅ MCP Execution: {integration['mcp_execution']}")
        print(f"✅ ACE Learning: {integration['ace_learning']}")
        print(f"✅ Logseq Storage: {integration['logseq_storage']}")
        print(f"✅ Knowledge Base: {integration['knowledge_base']}")

    # Get summary
    print("\n📊 Skills Development Summary")
    print("=" * 50)

    summary = await skills_primitive.get_skill_summary(context)
    print(f"Total Skills Developed: {summary['total_skills']}")
    print(f"Expert Level Skills: {len(summary['expert_skills'])}")

    for skill_name, overview in summary["skills_overview"].items():
        proficiency = overview["proficiency"]
        success_rate = overview["success_rate"]
        print(f"• {skill_name}: {proficiency} ({success_rate:.1%} success)")

    print("\n🎉 Enhanced Skills Management Benefits:")
    print("💾 Persistent storage in Logseq knowledge base")
    print("🤖 ACE framework integration for intelligent learning")
    print("🔒 Safe skill practice in MCP execution sandbox")
    print("📈 Cross-session skill improvement tracking")
    print("🔍 Knowledge base integration for context")

    return {
        "skills_developed": len(results),
        "integration_success": all(r["execution_success"] for r in results),
        "logseq_persistence": all(r["logseq_persistence"] for r in results),
        "summary": summary,
        "benefits": [
            "Persistent Logseq storage",
            "ACE framework learning",
            "Safe MCP execution",
            "Cross-session tracking",
            "Knowledge base integration",
        ],
    }


if __name__ == "__main__":
    asyncio.run(demonstrate_enhanced_skills())
