from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive


# 1. Define your core logic (The "Vibe")
async def generate_response(data: dict, context: WorkflowContext) -> dict:
    # TODO: Call your LLM here (OpenAI, Anthropic, etc.)
    prompt = data.get("prompt", "")
    return {"response": f"Processed: {prompt}"}


# 2. Compose the workflow (The "Reliability")
# Cache -> Retry -> Logic
workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_attempts=3) >> generate_response


# 3. Run it
async def main():
    context = WorkflowContext(workflow_id="vibe-run-1")
    result = await workflow.execute({"prompt": "Hello TTA!"}, context)
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
