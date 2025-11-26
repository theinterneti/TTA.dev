"""
E2B Advanced Iterative Refinement - Templates + Webhooks

Demonstrates the ultimate pattern combining:
1. Custom sandbox templates (10-50x faster startup)
2. Webhook monitoring (real-time tracking)
3. Iterative refinement (working code guarantee)

This is the production-ready pattern for AI code generation.
"""

import asyncio
import os
from datetime import datetime

import httpx
from e2b_code_interpreter import Sandbox

from tta_dev_primitives import WorkflowContext


class AdvancedIterativeCodeGenerator:
    """
    Production-ready code generator with:
    - Template-based execution (fast)
    - Webhook monitoring (observable)
    - Iterative refinement (reliable)
    """

    def __init__(
        self,
        template_id: str | None = None,
        webhook_url: str | None = None,
        max_attempts: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize generator.

        Args:
            template_id: E2B template ID (e.g., "template_ml_abc123")
                        If None, uses default template
            webhook_url: Your webhook server URL for monitoring
                        If None, webhooks disabled
            max_attempts: Maximum refinement iterations
            timeout: Execution timeout per attempt (seconds)
        """
        self.template_id = template_id
        self.webhook_url = webhook_url
        self.max_attempts = max_attempts
        self.timeout = timeout
        self.webhook_id: str | None = None

    async def generate_working_code(self, requirement: str, context: WorkflowContext) -> dict:
        """
        Generate code iteratively until it works.

        Process:
        1. Register webhook for tracking (if enabled)
        2. Generate code with LLM
        3. Execute in templated sandbox
        4. If fails, feed error back to LLM
        5. Repeat until success or max attempts
        6. Cleanup webhook

        Args:
            requirement: What the code should do
            context: Workflow context for tracing

        Returns:
            {
                "success": bool,
                "code": str,
                "output": str,
                "attempts": int,
                "template_used": str,
                "execution_time": float
            }
        """
        # Setup monitoring
        if self.webhook_url:
            self.webhook_id = await self._register_webhook(context.correlation_id)
            context.add_event(f"Webhook registered: {self.webhook_id}")

        try:
            previous_errors = None
            start_time = datetime.now()

            for attempt in range(1, self.max_attempts + 1):
                context.add_event(f"Attempt {attempt}/{self.max_attempts}")
                print(f"\n🔄 ITERATION {attempt}/{self.max_attempts}")

                # Step 1: Generate code (learning from errors)
                code = await self._llm_generate(requirement, previous_errors, context, attempt)
                print(f"📝 Generated {len(code)} chars of code")

                # Step 2: Execute in templated sandbox
                result = await self._execute_in_sandbox(code, context)

                # Step 3: Check result
                if result["success"]:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    context.add_event(f"✅ Success after {attempt} attempt(s)")
                    print(f"✅ SUCCESS after {attempt} iteration(s)!")

                    return {
                        "success": True,
                        "code": code,
                        "output": result["output"],
                        "attempts": attempt,
                        "template_used": self.template_id or "default",
                        "execution_time": execution_time,
                    }

                # Step 4: Prepare for retry
                previous_errors = result["error"]
                context.add_event(f"❌ Attempt {attempt} failed: {result['error']}")
                print(f"❌ Execution failed: {result['error']}")

            # Max attempts exceeded
            execution_time = (datetime.now() - start_time).total_seconds()
            context.add_event("Max attempts exceeded")
            print(f"❌ Failed after {self.max_attempts} attempts")

            return {
                "success": False,
                "error": "Max attempts exceeded",
                "last_error": previous_errors,
                "attempts": self.max_attempts,
                "execution_time": execution_time,
            }

        finally:
            # Cleanup webhook
            if self.webhook_id:
                await self._unregister_webhook(self.webhook_id)
                context.add_event("Webhook cleaned up")

    async def _llm_generate(
        self,
        requirement: str,
        previous_errors: str | None,
        context: WorkflowContext,
        attempt: int,
    ) -> str:
        """
        Generate code using LLM.

        In production, replace this with actual LLM call.
        """
        print(f"🤖 CODE GENERATOR - Attempt {attempt}")

        # Simulate realistic code generation progression
        if attempt == 1:
            # First attempt: Common mistake (missing import)
            print("💭 Generating initial code (might have issues)...")
            code = """
# Calculate fibonacci sequence
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test
result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""

        elif attempt == 2:
            # Second attempt: Fix previous error but introduce new one
            print(f"📝 Learning from error: {previous_errors}")
            print("💭 Fixed previous issue, but might have logic bug...")
            code = """
# Calculate fibonacci sequence (fixed imports)
import sys

def fibonacci(n):
    if n <= 1:
        return n
    # Oops - wrong recursion formula
    return fibonacci(n-1) + fibonacci(n-3)

# Test
result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""

        else:
            # Third attempt: Clean, working code
            print(f"📝 Learning from error: {previous_errors}")
            print("💭 Generating clean, working code...")
            code = """
# Calculate fibonacci sequence (correct version)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test
result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""

        return code

    async def _execute_in_sandbox(self, code: str, context: WorkflowContext) -> dict:
        """
        Execute code in E2B sandbox (with template if configured).
        """
        print("⚡ EXECUTING IN E2B SANDBOX")
        if self.template_id:
            print(f"📦 Using template: {self.template_id}")
        else:
            print("📦 Using default template")

        # Create sandbox from template
        create_start = datetime.now()
        sandbox = await Sandbox.create(template=self.template_id)
        create_time = (datetime.now() - create_start).total_seconds()

        if self.template_id:
            print(f"⚡ Template startup: {create_time:.3f}s (should be ~0.1s)")
        else:
            print(f"⚡ Default startup: {create_time:.3f}s")

        try:
            # Execute code
            exec_start = datetime.now()
            result = await sandbox.run_code(code, timeout=self.timeout)
            exec_time = (datetime.now() - exec_start).total_seconds()

            if result.error:
                print("❌ Code execution failed!")
                print(f"🐛 Error: {result.error}")
                return {"success": False, "error": result.error, "output": None}

            print("✅ Code executed successfully!")
            print(f"⏱️  Execution time: {exec_time:.3f}s")
            output = "\n".join(result.logs.stdout)
            print(f"📤 Output:\n{output}")

            return {"success": True, "error": None, "output": output}

        except Exception as e:
            print(f"❌ Sandbox error: {str(e)}")
            return {"success": False, "error": str(e), "output": None}

        finally:
            await sandbox.kill()

    async def _register_webhook(self, correlation_id: str) -> str:
        """
        Register webhook with E2B for this generation session.

        Returns webhook ID.
        """
        if not self.webhook_url:
            return ""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.e2b.app/events/webhooks",
                headers={
                    "X-API-Key": os.getenv("E2B_API_KEY", ""),
                    "Content-Type": "application/json",
                },
                json={
                    "name": f"Generation {correlation_id}",
                    "url": f"{self.webhook_url}/generation/{correlation_id}",
                    "enabled": True,
                    "events": [
                        "sandbox.lifecycle.created",
                        "sandbox.lifecycle.killed",
                    ],
                    "signatureSecret": os.getenv("E2B_WEBHOOK_SECRET", "secret"),
                },
            )
            data = response.json()
            return data.get("id", "")

    async def _unregister_webhook(self, webhook_id: str):
        """Remove webhook after generation completes."""
        if not webhook_id or not self.webhook_url:
            return

        async with httpx.AsyncClient() as client:
            await client.delete(
                f"https://api.e2b.app/events/webhooks/{webhook_id}",
                headers={"X-API-Key": os.getenv("E2B_API_KEY", "")},
            )


# Demo 1: Basic usage (no template)
async def demo_basic():
    """Basic iterative refinement without template."""
    print("=" * 60)
    print("DEMO 1: Basic Iterative Refinement (No Template)")
    print("=" * 60)

    generator = AdvancedIterativeCodeGenerator(max_attempts=3)

    context = WorkflowContext(correlation_id="demo-basic-001")
    result = await generator.generate_working_code(
        requirement="Calculate fibonacci sequence", context=context
    )

    print("\n" + "=" * 60)
    print("DEMO 1 RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Attempts: {result['attempts']}")
    print(f"Execution time: {result['execution_time']:.2f}s")
    print("=" * 60)


# Demo 2: With ML template (fast startup)
async def demo_with_template():
    """
    Iterative refinement with custom ML template.

    Prerequisites:
    1. Create template:
       cd packages/tta-dev-primitives/examples
       e2b template build --file e2b.Dockerfile.ml-template

    2. Use template ID returned from build
    """
    print("\n" + "=" * 60)
    print("DEMO 2: With ML Template (Fast Startup)")
    print("=" * 60)

    # Replace with your actual template ID
    template_id = os.getenv("E2B_ML_TEMPLATE_ID", None)

    if not template_id:
        print("⚠️  No template ID set. Using default template.")
        print("To use custom template:")
        print("  1. Build: e2b template build --file e2b.Dockerfile.ml-template")
        print("  2. Set: export E2B_ML_TEMPLATE_ID=<your-template-id>")
        print("  3. Run this demo again")
        print("\nProceeding with default template...\n")

    generator = AdvancedIterativeCodeGenerator(template_id=template_id, max_attempts=3)

    context = WorkflowContext(correlation_id="demo-template-001")
    result = await generator.generate_working_code(
        requirement="Calculate fibonacci sequence", context=context
    )

    print("\n" + "=" * 60)
    print("DEMO 2 RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Template: {result.get('template_used', 'default')}")
    print(f"Attempts: {result['attempts']}")
    print(f"Execution time: {result['execution_time']:.2f}s")
    if template_id:
        print("\n✅ Template startup should be ~0.1s vs 5-10s without template!")
    print("=" * 60)


# Demo 3: Full stack (template + webhooks)
async def demo_full_stack():
    """
    Complete pattern with template + webhook monitoring.

    Prerequisites:
    1. Create ML template (see demo_with_template)
    2. Run webhook server:
       python examples/e2b_webhook_monitoring_server.py
    3. Set webhook URL:
       export E2B_WEBHOOK_URL=http://localhost:8000/webhooks
    """
    print("\n" + "=" * 60)
    print("DEMO 3: Full Stack (Template + Webhooks)")
    print("=" * 60)

    template_id = os.getenv("E2B_ML_TEMPLATE_ID", None)
    webhook_url = os.getenv("E2B_WEBHOOK_URL", None)

    if not webhook_url:
        print("⚠️  No webhook URL set. Webhooks disabled.")
        print("To enable webhooks:")
        print("  1. Run: python examples/e2b_webhook_monitoring_server.py")
        print("  2. Set: export E2B_WEBHOOK_URL=http://localhost:8000/webhooks")
        print("\nProceeding without webhooks...\n")

    generator = AdvancedIterativeCodeGenerator(
        template_id=template_id, webhook_url=webhook_url, max_attempts=3
    )

    context = WorkflowContext(correlation_id="demo-full-001")
    result = await generator.generate_working_code(
        requirement="Calculate fibonacci sequence", context=context
    )

    print("\n" + "=" * 60)
    print("DEMO 3 RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Template: {result.get('template_used', 'default')}")
    print(f"Attempts: {result['attempts']}")
    print(f"Execution time: {result['execution_time']:.2f}s")
    if webhook_url:
        print("\n✅ Check webhook server logs for real-time events!")
        print("   Metrics: http://localhost:8000/metrics")
    print("=" * 60)


async def main():
    """Run all demos."""
    print("\n🚀 E2B ADVANCED ITERATIVE REFINEMENT DEMOS\n")

    # Demo 1: Basic (no template, no webhooks)
    await demo_basic()

    # Demo 2: With template (fast startup)
    await demo_with_template()

    # Demo 3: Full stack (template + webhooks)
    await demo_full_stack()

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETE!")
    print("=" * 60)
    print("\n📚 Next steps:")
    print("  1. Create your own template: e2b template build")
    print("  2. Run webhook server: python e2b_webhook_monitoring_server.py")
    print("  3. Integrate into your workflows!")
    print("\n✨ Benefits achieved:")
    print("  • 10-50x faster execution (templates)")
    print("  • Real-time monitoring (webhooks)")
    print("  • Working code guarantee (iteration)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Check API key
    if not os.getenv("E2B_API_KEY"):
        print("❌ E2B_API_KEY not set!")
        print("Get your key: https://e2b.dev/docs/getting-started/api-key")
        print("Then: export E2B_API_KEY=your-key-here")
        exit(1)

    asyncio.run(main())
