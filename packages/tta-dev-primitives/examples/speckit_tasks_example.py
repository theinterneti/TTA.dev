"""
TasksPrimitive Examples - Demonstrating Key Features

Five examples showing TasksPrimitive's capabilities:
1. Basic task generation from plan.md
2. Task ordering with dependencies
3. Multiple output formats
4. Complete Plan → Tasks workflow
5. Parallel work stream identification
"""

import asyncio
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.speckit import PlanPrimitive, TasksPrimitive


async def example_1_basic():
    """Example 1: Basic task generation"""
    print("\n" + "=" * 80)
    print("Example 1: Basic Task Generation")
    print("=" * 80 + "\n")

    output_dir = Path("examples/tasks_output/example1")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create sample plan
    plan_content = """# LRU Cache Implementation

## Phase 1: Setup (1 day, 8h)
- [ ] Project structure (4h)
- [ ] Build system (4h)

## Phase 2: Implementation (3 days, 24h)
- [ ] LRU eviction (12h)
- [ ] TTL support (12h)

## Phase 3: Testing (1 day, 8h)
- [ ] Unit tests (4h)
- [ ] Integration tests (4h)
"""
    plan_path = output_dir / "plan.md"
    plan_path.write_text(plan_content, encoding="utf-8")

    # Generate tasks
    primitive = TasksPrimitive(
        output_dir=str(output_dir),
        include_effort=True,
        identify_critical_path=True,
    )

    result = await primitive.execute({"plan_path": str(plan_path)}, WorkflowContext())

    print(f"✅ Generated {len(result['tasks'])} tasks")
    print(f"📁 Output: {result['tasks_path']}")
    if result.get("critical_path"):
        print(f"🎯 Critical path: {len(result['critical_path'])} tasks")


async def example_2_dependencies():
    """Example 2: Dependency ordering"""
    print("\n" + "=" * 80)
    print("Example 2: Task Ordering with Dependencies")
    print("=" * 80 + "\n")

    output_dir = Path("examples/tasks_output/example2")
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_content = """# API Platform

## Phase 1: Foundation (2 days, 16h)
- [ ] Database schema (8h) [T-001]
- [ ] Auth setup (8h) [T-002]

## Phase 2: API (3 days, 24h)
- [ ] User endpoints (depends: T-001, T-002) (12h) [T-003]
- [ ] Data endpoints (depends: T-001) (12h) [T-004]

## Phase 3: Testing (2 days, 16h)
- [ ] Unit tests (depends: T-003, T-004) (8h) [T-005]
- [ ] Integration tests (depends: T-005) (8h) [T-006]
"""
    plan_path = output_dir / "plan.md"
    plan_path.write_text(plan_content, encoding="utf-8")

    primitive = TasksPrimitive(output_dir=str(output_dir))
    result = await primitive.execute({"plan_path": str(plan_path)}, WorkflowContext())

    print("✅ Tasks ordered by dependencies:")
    for task in result["tasks"][:6]:
        deps = task.get("dependencies", [])
        dep_str = f" (depends: {', '.join(deps)})" if deps else ""
        print(f"   {task['id']}: {task['title']}{dep_str}")


async def example_3_formats():
    """Example 3: Multiple output formats"""
    print("\n" + "=" * 80)
    print("Example 3: Multiple Output Formats")
    print("=" * 80 + "\n")

    output_dir = Path("examples/tasks_output/example3")
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_content = """# Multi-Format Demo

## Phase 1: Setup (1 day, 8h)
- [ ] Initialize project (4h)
- [ ] Setup dependencies (4h)
"""
    plan_path = output_dir / "plan.md"
    plan_path.write_text(plan_content, encoding="utf-8")

    # Generate in multiple formats
    for fmt in ["markdown", "json", "jira", "linear", "github"]:
        primitive = TasksPrimitive(output_dir=str(output_dir), output_format=fmt)
        result = await primitive.execute(
            {"plan_path": str(plan_path)}, WorkflowContext()
        )
        print(f"✅ {fmt:10s}: {result['tasks_path']}")


async def example_4_workflow():
    """Example 4: Complete Spec → Plan → Tasks workflow"""
    print("\n" + "=" * 80)
    print("Example 4: Complete Workflow")
    print("=" * 80 + "\n")

    output_dir = Path("examples/tasks_output/example4")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create spec
    spec_content = """# User Authentication System

## Requirements
- FR1: Email/password registration
- FR2: JWT-based login
- FR3: Password reset
- NFR1: Support 1000+ concurrent users
"""
    spec_path = output_dir / "spec.md"
    spec_path.write_text(spec_content, encoding="utf-8")
    print("1️⃣ Created spec.md")

    # Generate plan
    plan_primitive = PlanPrimitive(output_dir=str(output_dir))
    plan_result = await plan_primitive.execute(
        {"spec_path": str(spec_path)}, WorkflowContext()
    )
    print(f"2️⃣ Generated plan: {plan_result['plan_path']}")

    # Generate tasks
    tasks_primitive = TasksPrimitive(
        output_dir=str(output_dir), identify_critical_path=True
    )
    tasks_result = await tasks_primitive.execute(
        {"plan_path": plan_result["plan_path"]}, WorkflowContext()
    )
    print(f"3️⃣ Generated {len(tasks_result['tasks'])} tasks")
    print("\n✅ Complete workflow: Spec → Plan → Tasks")


async def example_5_parallel():
    """Example 5: Parallel work streams"""
    print("\n" + "=" * 80)
    print("Example 5: Parallel Work Streams")
    print("=" * 80 + "\n")

    output_dir = Path("examples/tasks_output/example5")
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_content = """# Full-Stack App

## Phase 1: Foundation (2 days, 16h)
- [ ] Database schema (8h) [T-001]
- [ ] API framework (8h) [T-002]

## Phase 2: Backend (3 days, 24h)
- [ ] Auth API (depends: T-001) (8h) [T-003]
- [ ] User API (depends: T-001) (8h) [T-004]
- [ ] Data API (depends: T-001) (8h) [T-005]

## Phase 3: Frontend (3 days, 24h)
- [ ] Login UI (depends: T-002) (8h) [T-006]
- [ ] Dashboard UI (depends: T-002) (8h) [T-007]
- [ ] Settings UI (depends: T-002) (8h) [T-008]
"""
    plan_path = output_dir / "plan.md"
    plan_path.write_text(plan_content, encoding="utf-8")

    primitive = TasksPrimitive(
        output_dir=str(output_dir),
        group_parallel_work=True,
        identify_critical_path=True,
    )
    result = await primitive.execute({"plan_path": str(plan_path)}, WorkflowContext())

    print("✅ Parallel work streams identified!")
    if result.get("parallel_streams"):
        for i, stream in enumerate(result["parallel_streams"][:3], 1):
            tasks = stream.get("tasks", [])
            print(f"\n🔀 Stream {i}: {len(tasks)} tasks can run in parallel")
            for t in tasks[:3]:
                print(f"   - {t['title']}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("TasksPrimitive - Comprehensive Examples")
    print("=" * 80)

    await example_1_basic()
    await example_2_dependencies()
    await example_3_formats()
    await example_4_workflow()
    await example_5_parallel()

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)
    print("\n📁 Check examples/tasks_output/ for generated files\n")


if __name__ == "__main__":
    asyncio.run(main())
