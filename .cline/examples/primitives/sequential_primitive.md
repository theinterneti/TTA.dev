# SequentialPrimitive Examples for Cline

**Purpose:** Learn how to chain workflow operations in sequence with TTA.dev's SequentialPrimitive

## Example 1: Multi-Step Data Processing Pipeline

**When to Use:** You have a series of transformations that must happen in order (extract → transform → load)

**Cline Prompt Example:**

```
I need to process user data through multiple validation and transformation steps.
Set up a pipeline: validate_input → enrich_data → persist_results
```

**Expected Implementation:**

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

class DataProcessingPipeline:
    def __init__(self):
        # Chain processing steps in sequence
        self.pipeline = (
            self.validate_input >>        # Step 1: Validate
            self.enrich_data >>           # Step 2: Enrich
            self.persist_results          # Step 3: Save
        )

    async def process_user_data(self, user_data: dict) -> dict:
        context = WorkflowContext(
            workflow_id="data-pipeline",
            metadata={"user_id": user_data.get("id")}
        )
        return await self.pipeline.execute(user_data, context)

    async def validate_input(self, data: dict) -> dict:
        """Step 1: Validate input data"""
        # Validation logic
        if not data.get("email"):
            raise ValueError("Email is required")

        # Add validation metadata
        context.metadata["validation_passed"] = True
        return data

    async def enrich_data(self, data: dict) -> dict:
        """Step 2: Enrich with additional information"""
        # Enrichment logic (e.g., fetch from external APIs)
        data["full_name"] = f"{data.get('first_name', '')} {data.get('last_name', '')}"
        data["processed_at"] = "2025-11-08T11:00:00Z"

        context.metadata["enrichment_complete"] = True
        return data

    async def persist_results(self, data: dict) -> dict:
        """Step 3: Save to database"""
        # Persistence logic
        # context.metadata tracks the entire pipeline
        return {
            "status": "success",
            "user_id": data.get("id"),
            "processed_data": data
        }
```

## Example 2: Agent Workflow Coordination

**When to Use:** Multi-agent systems where agents work in sequence (research → analysis → reporting)

**Cline Prompt Example:**

```
Create an agent workflow: research_agent → analysis_agent → report_agent
Each agent passes results to the next agent in the chain.
```

**Expected Implementation:**

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

class ResearchWorkflow:
    def __init__(self):
        # Sequential agent execution
        self.agent_pipeline = (
            self.research_agent >>      # Research topic
            self.analysis_agent >>      # Analyze findings
            self.report_agent           # Generate report
        )

    async def conduct_research(self, topic: str) -> dict:
        context = WorkflowContext(
            workflow_id="research-workflow",
            metadata={"topic": topic, "stage": "start"}
        )
        return await self.agent_pipeline.execute(
            {"topic": topic, "scope": "comprehensive"},
            context
        )

    async def research_agent(self, data: dict) -> dict:
        """Step 1: Research the topic"""
        context = WorkflowContext.get_current()  # Get context from pipeline
        context.metadata["stage"] = "research"

        # Research implementation
        findings = await self._search_and_collect(data["topic"])

        return {
            "stage": "research_complete",
            "findings": findings,
            "sources": findings.get("sources", []),
            "topic": data["topic"]
        }

    async def analysis_agent(self, data: dict) -> dict:
        """Step 2: Analyze research findings"""
        context = WorkflowContext.get_current()
        context.metadata["stage"] = "analysis"

        # Analysis implementation
        analysis = await self._analyze_findings(data["findings"])

        return {
            "stage": "analysis_complete",
            "insights": analysis["insights"],
            "recommendations": analysis["recommendations"],
            "confidence_score": analysis["confidence"],
            "original_topic": data["topic"]
        }

    async def report_agent(self, data: dict) -> dict:
        """Step 3: Generate final report"""
        context = WorkflowContext.get_current()
        context.metadata["stage"] = "reporting"

        # Report generation
        report = await self._generate_report(
            topic=data["original_topic"],
            insights=data["insights"],
            recommendations=data["recommendations"]
        )

        return {
            "stage": "complete",
            "report": report,
            "metadata": context.metadata  # Full pipeline history
        }
```

## Example 3: API Request Pipeline with Error Handling

**When to Use:** Multi-step API interactions with validation and transformation at each step

**Cline Prompt Example:**

```
Build an API request pipeline: prepare_request → authenticate → send_request → process_response
Include error handling and logging at each step.
```

**Expected Implementation:**

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

class APIClient:
    def __init__(self):
        self.request_pipeline = (
            self.prepare_request >>       # Step 1: Prepare
            self.authenticate >>          # Step 2: Auth
            self.send_request >>          # Step 3: Send
            self.process_response         # Step 4: Process
        )

    async def make_api_call(self, endpoint: str, data: dict) -> dict:
        context = WorkflowContext(
            workflow_id="api-call",
            metadata={"endpoint": endpoint, "timestamp": "2025-11-08T11:00:00Z"}
        )
        return await self.request_pipeline.execute(
            {"endpoint": endpoint, "payload": data},
            context
        )

    async def prepare_request(self, data: dict) -> dict:
        """Step 1: Prepare and validate request"""
        context = WorkflowContext.get_current()

        # Validation
        if not data["endpoint"]:
            raise ValueError("Endpoint is required")

        # Preparation
        prepared = {
            "url": f"https://api.example.com/{data['endpoint']}",
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "TTA-Dev-Client/1.0"
            },
            "payload": data["payload"]
        }

        context.metadata["request_prepared"] = True
        return prepared

    async def authenticate(self, data: dict) -> dict:
        """Step 2: Add authentication"""
        context = WorkflowContext.get_current()

        # Add auth token
        data["headers"]["Authorization"] = "Bearer your-token-here"

        context.metadata["authenticated"] = True
        return data

    async def send_request(self, data: dict) -> dict:
        """Step 3: Send HTTP request"""
        context = WorkflowContext.get_current()

        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                data["url"],
                headers=data["headers"],
                json=data["payload"]
            ) as response:
                response_data = await response.json()

                context.metadata.update({
                    "http_status": response.status,
                    "response_size": len(str(response_data))
                })

                return {
                    "response": response_data,
                    "status_code": response.status,
                    "request_data": data
                }

    async def process_response(self, data: dict) -> dict:
        """Step 4: Process and validate response"""
        context = WorkflowContext.get_current()

        if data["status_code"] != 200:
            raise ValueError(f"API request failed: {data['status_code']}")

        # Process response
        processed = {
            "success": True,
            "data": data["response"],
            "request_info": {
                "endpoint": data["request_data"]["url"],
                "processed_at": context.metadata.get("timestamp")
            },
            "pipeline_metadata": context.metadata
        }

        return processed
```

## Example 4: File Processing Workflow

**When to Use:** File processing with multiple transformations (read → validate → transform → compress → store)

**Cline Prompt Example:**

```
Set up a file processing workflow: read_file → validate_content → transform → compress → upload_to_s3
Each step should pass results to the next step.
```

**Expected Implementation:**

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
import aiofiles
import gzip
import json

class FileProcessor:
    def __init__(self):
        self.file_pipeline = (
            self.read_file >>           # Step 1: Read
            self.validate_content >>     # Step 2: Validate
            self.transform_data >>       # Step 3: Transform
            self.compress_file >>        # Step 4: Compress
            self.upload_to_s3           # Step 5: Upload
        )

    async def process_file(self, file_path: str, target_bucket: str) -> dict:
        context = WorkflowContext(
            workflow_id="file-processing",
            metadata={"file_path": file_path, "target_bucket": target_bucket}
        )
        return await self.file_pipeline.execute(
            {"file_path": file_path, "target_bucket": target_bucket},
            context
        )

    async def read_file(self, data: dict) -> dict:
        """Step 1: Read file contents"""
        context = WorkflowContext.get_current()

        async with aiofiles.open(data["file_path"], 'r') as f:
            content = await f.read()

        return {
            "original_content": content,
            "file_path": data["file_path"],
            "target_bucket": data["target_bucket"]
        }

    async def validate_content(self, data: dict) -> dict:
        """Step 2: Validate file content"""
        context = WorkflowContext.get_current()

        # Validation logic (e.g., JSON validation, schema check)
        try:
            json.loads(data["original_content"])
            is_valid = True
        except json.JSONDecodeError:
            is_valid = False

        if not is_valid:
            raise ValueError("Invalid file format")

        context.metadata["validation_passed"] = True
        return data

    async def transform_data(self, data: dict) -> dict:
        """Step 3: Transform content"""
        context = WorkflowContext.get_current()

        # Transformation logic
        parsed = json.loads(data["original_content"])
        transformed = {
            "records": parsed,
            "record_count": len(parsed),
            "processing_date": "2025-11-08T11:00:00Z"
        }

        context.metadata["transformation_complete"] = True
        return {
            **data,
            "transformed_content": transformed
        }

    async def compress_file(self, data: dict) -> dict:
        """Step 4: Compress the data"""
        context = WorkflowContext.get_current()

        # Compress with gzip
        content_str = json.dumps(data["transformed_content"])
        compressed = gzip.compress(content_str.encode('utf-8'))

        context.metadata["compression_ratio"] = len(compressed) / len(content_str)
        return {
            **data,
            "compressed_content": compressed,
            "compressed_size": len(compressed)
        }

    async def upload_to_s3(self, data: dict) -> dict:
        """Step 5: Upload to S3"""
        context = WorkflowContext.get_current()

        # S3 upload logic (using boto3 or similar)
        s3_key = f"processed/{data['file_path'].split('/')[-1]}.gz"

        # Simulate S3 upload
        context.metadata.update({
            "s3_key": s3_key,
            "upload_complete": True
        })

        return {
            "success": True,
            "s3_key": s3_key,
            "original_size": len(data["original_content"]),
            "compressed_size": data["compressed_size"],
            "compression_ratio": context.metadata["compression_ratio"],
            "pipeline_metadata": context.metadata
        }
```

## Cline Detection Patterns

**SequentialPrimitive Indicators:**

- "pipeline"
- "chain"
- "workflow"
- "step by step"
- "multi-step"
- "one after another"
- "process in order"

**Cline's Response Strategy:**

1. Identify the sequence of operations
2. Break down into logical steps
3. Use >> operator to chain steps
4. Add proper WorkflowContext for tracing
5. Include error handling between steps

## Best Practices

### Step Interface Consistency

```python
# All steps should have consistent interface
async def step_name(self, data: dict) -> dict:
    # Process data
    return processed_data
```

### Context Propagation

```python
# Use WorkflowContext to track pipeline state
context = WorkflowContext.get_current()
context.metadata["step_completed"] = step_name
```

### Error Handling

```python
# Let failures bubble up or handle per-step
try:
    return await next_step.execute(data, context)
except SpecificError as e:
    # Handle specific errors
    context.metadata["error"] = str(e)
    raise
```

## Common Mistakes to Avoid

❌ **Wrong:** Manual chaining

```python
# Manual step chaining - error prone
result1 = await step1.execute(data, context)
result2 = await step2.execute(result1, context)
return await step3.execute(result2, context)
```

✅ **Right:** Use SequentialPrimitive

```python
# Clean composition
pipeline = step1 >> step2 >> step3
return await pipeline.execute(data, context)
```

❌ **Wrong:** No context propagation

```python
# Context gets lost between steps
pipeline = step1 >> step2 >> step3
# How to track what happened at each step?
```

✅ **Right:** Use WorkflowContext

```python
# Full pipeline tracking
pipeline = step1 >> step2 >> step3
result = await pipeline.execute(data, context)
# context.metadata has complete pipeline history
```

---

**Next Steps:** When cline detects sequential workflow patterns, it should suggest SequentialPrimitive with appropriate step composition and context tracking.


---
**Logseq:** [[TTA.dev/.cline/Examples/Primitives/Sequential_primitive]]
