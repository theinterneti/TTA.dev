# Agent Coordination Patterns - Multi-Agent Workflows

**Purpose:** Learn how to build complex multi-agent systems with state management, coordination patterns, and intelligent task distribution

## Example 1: Research-Analysis-Writing Pipeline

**When to Use:** Creating a comprehensive research and content generation pipeline with specialized agents

**Cline Prompt Example:**

```
I need to build a research pipeline where one agent gathers information,
another analyzes it, and a third creates a final report. Include
proper state management and error handling between agents.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive, LearningMode
import asyncio
from typing import Any, Dict, List, Optional
import json

class SharedWorkflowState:
    """Shared state management for multi-agent workflows"""

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.research_data: Dict[str, Any] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.written_content: Dict[str, Any] = {}
        self.agent_performance: Dict[str, Dict[str, float]] = {}
        self.error_log: List[dict] = []
        self.success_metrics: Dict[str, Any] = {}
        self.current_stage = "initializing"
        self.stage_outputs: Dict[str, Any] = {}

    def update_stage(self, stage: str, data: Any):
        """Update workflow stage with data"""
        self.current_stage = stage
        self.stage_outputs[stage] = data
        self.success_metrics[f"{stage}_completed"] = True

    def log_error(self, agent: str, error: Exception, context: dict):
        """Log error with context"""
        self.error_log.append({
            "agent": agent,
            "error": str(error),
            "context": context,
            "timestamp": asyncio.get_event_loop().time(),
            "stage": self.current_stage
        })

    def update_performance(self, agent: str, metrics: Dict[str, float]):
        """Update agent performance metrics"""
        if agent not in self.agent_performance:
            self.agent_performance[agent] = {}
        self.agent_performance[agent].update(metrics)

class ResearchAgent:
    """Specialized agent for data gathering and research"""

    def __init__(self, state: SharedWorkflowState):
        self.state = state
        self.name = "research_agent"
        self.retry_primitive = AdaptiveRetryPrimitive(
            target_primitive=self._execute_research,
            learning_mode=LearningMode.VALIDATE,
            max_retries=3
        )

    async def research(self, topic: str, depth: str = "standard", sources_needed: int = 5) -> dict:
        """Execute research with retry and fallback"""
        self.state.update_stage("researching", {"topic": topic, "depth": depth})

        context = WorkflowContext(
            workflow_id=self.state.workflow_id,
            metadata={
                "agent": self.name,
                "topic": topic,
                "depth": depth,
                "sources_needed": sources_needed
            }
        )

        try:
            result = await self.retry_primitive.execute(
                {"topic": topic, "depth": depth, "sources_needed": sources_needed},
                context
            )

            self.state.research_data = result
            self.state.update_stage("research_completed", result)
            self.state.update_performance(self.name, {
                "success_rate": 1.0,
                "avg_response_time": result.get("research_time", 0),
                "sources_collected": result.get("sources_count", 0)
            })

            return result

        except Exception as e:
            self.state.log_error(self.name, e, {"topic": topic, "depth": depth})
            return self._fallback_research(topic)

    async def _execute_research(self, data: dict) -> dict:
        """Execute actual research operation"""
        topic = data["topic"]
        depth = data["depth"]
        sources_needed = data["sources_needed"]

        start_time = asyncio.get_event_loop().time()

        # Simulate research process
        await asyncio.sleep(2 if depth == "deep" else 1)

        # Simulate variable success based on topic complexity
        if "quantum" in topic.lower() or "blockchain" in topic.lower():
            if depth == "standard":
                raise ConnectionError("Research API temporarily unavailable")

        research_data = {
            "topic": topic,
            "depth": depth,
            "sources_count": sources_needed,
            "key_findings": [
                f"Finding 1 about {topic}",
                f"Finding 2 about {topic}",
                f"Finding 3 about {topic}"
            ],
            "data_quality": "high" if depth == "deep" else "medium",
            "research_time": asyncio.get_event_loop().time() - start_time,
            "sources": [f"Source {i+1}" for i in range(sources_needed)],
            "methodology": "comprehensive_web_search" if depth == "deep" else "targeted_search"
        }

        return research_data

    def _fallback_research(self, topic: str) -> dict:
        """Fallback research when primary fails"""
        return {
            "topic": topic,
            "depth": "basic",
            "sources_count": 3,
            "key_findings": [f"Basic finding about {topic}"],
            "data_quality": "basic",
            "research_time": 0.5,
            "sources": ["Source 1", "Source 2", "Source 3"],
            "methodology": "fallback_search",
            "fallback_used": True
        }

class AnalysisAgent:
    """Specialized agent for data analysis and insights"""

    def __init__(self, state: SharedWorkflowState):
        self.state = state
        self.name = "analysis_agent"
        self.parallel_analysis = ParallelPrimitive([])

    async def analyze(self, research_data: dict, analysis_type: str = "comprehensive") -> dict:
        """Execute analysis with fallback options"""
        self.state.update_stage("analyzing", {"analysis_type": analysis_type})

        context = WorkflowContext(
            workflow_id=self.state.workflow_id,
            metadata={
                "agent": self.name,
                "analysis_type": analysis_type,
                "input_quality": research_data.get("data_quality", "unknown")
            }
        )

        try:
            # Create analysis pipeline based on type
            if analysis_type == "comprehensive":
                result = await self._comprehensive_analysis(research_data, context)
            elif analysis_type == "quick":
                result = await self._quick_analysis(research_data, context)
            else:
                result = await self._basic_analysis(research_data, context)

            self.state.analysis_results = result
            self.state.update_stage("analysis_completed", result)
            self.state.update_performance(self.name, {
                "success_rate": 1.0,
                "analysis_depth": analysis_type,
                "insights_generated": len(result.get("insights", []))
            })

            return result

        except Exception as e:
            self.state.log_error(self.name, e, {"analysis_type": analysis_type})
            return self._fallback_analysis(research_data)

    async def _comprehensive_analysis(self, research_data: dict, context: WorkflowContext) -> dict:
        """Perform comprehensive analysis with multiple analytical approaches"""
        start_time = asyncio.get_event_loop().time()

        # Parallel analysis of different aspects
        trend_analysis = self._analyze_trends(research_data)
        gap_analysis = self._analyze_gaps(research_data)
        opportunity_analysis = self._analyze_opportunities(research_data)

        # Execute analyses in parallel
        analyses = await asyncio.gather(
            trend_analysis,
            gap_analysis,
            opportunity_analysis,
            return_exceptions=True
        )

        trend_result, gap_result, opportunity_result = analyses

        analysis_result = {
            "insights": [
                "Strategic insight 1 based on comprehensive analysis",
                "Strategic insight 2 from trend analysis",
                "Key opportunity identified in gap analysis"
            ],
            "trends": trend_result if not isinstance(trend_result, Exception) else ["trend_analysis_failed"],
            "gaps": gap_result if not isinstance(gap_result, Exception) else ["gap_analysis_failed"],
            "opportunities": opportunity_result if not isinstance(opportunity_result, Exception) else ["opportunity_analysis_failed"],
            "recommendations": [
                "Recommendation 1: Focus on identified trends",
                "Recommendation 2: Address critical gaps",
                "Recommendation 3: Capitalize on opportunities"
            ],
            "confidence_score": 0.88,
            "analysis_time": asyncio.get_event_loop().time() - start_time,
            "methodology": "comprehensive_multi_approach"
        }

        return analysis_result

    async def _quick_analysis(self, research_data: dict, context: WorkflowContext) -> dict:
        """Quick analysis for time-sensitive decisions"""
        await asyncio.sleep(0.8)  # Fast analysis

        return {
            "insights": ["Quick insight 1", "Quick insight 2"],
            "trends": ["Trend 1"],
            "recommendations": ["Quick recommendation"],
            "confidence_score": 0.75,
            "analysis_time": 0.8,
            "methodology": "rapid_assessment"
        }

    async def _basic_analysis(self, research_data: dict, context: WorkflowContext) -> dict:
        """Basic analysis for simple use cases"""
        await asyncio.sleep(0.5)

        return {
            "insights": ["Basic insight"],
            "trends": ["Basic trend"],
            "recommendations": ["Basic recommendation"],
            "confidence_score": 0.65,
            "analysis_time": 0.5,
            "methodology": "basic_summary"
        }

    async def _analyze_trends(self, research_data: dict) -> list:
        """Analyze trends in research data"""
        await asyncio.sleep(0.3)
        return ["Emerging trend 1", "Emerging trend 2"]

    async def _analyze_gaps(self, research_data: dict) -> list:
        """Analyze gaps in research data"""
        await asyncio.sleep(0.4)
        return ["Gap 1 identified", "Gap 2 identified"]

    async def _analyze_opportunities(self, research_data: dict) -> list:
        """Analyze opportunities in research data"""
        await asyncio.sleep(0.3)
        return ["Opportunity 1", "Opportunity 2"]

    def _fallback_analysis(self, research_data: dict) -> dict:
        """Fallback analysis when primary fails"""
        return {
            "insights": ["Basic insight from fallback analysis"],
            "trends": ["Basic trend"],
            "gaps": ["Basic gap"],
            "opportunities": ["Basic opportunity"],
            "recommendations": ["Use fallback recommendations"],
            "confidence_score": 0.50,
            "analysis_time": 0.1,
            "methodology": "fallback_basic",
            "fallback_used": True
        }

class WritingAgent:
    """Specialized agent for content generation and writing"""

    def __init__(self, state: SharedWorkflowState):
        self.state = state
        self.name = "writing_agent"
        self.fallback_writing = FallbackPrimitive(
            primary=self._execute_writing,
            fallbacks=[self._alternative_writing, self._emergency_writing]
        )

    async def write(self, analysis_data: dict, style: str = "professional", audience: str = "general") -> dict:
        """Execute writing with multiple fallback options"""
        self.state.update_stage("writing", {"style": style, "audience": audience})

        context = WorkflowContext(
            workflow_id=self.state.workflow_id,
            metadata={
                "agent": self.name,
                "writing_style": style,
                "target_audience": audience,
                "input_confidence": analysis_data.get("confidence_score", 0)
            }
        )

        try:
            result = await self.fallback_writing.execute(
                {"analysis_data": analysis_data, "style": style, "audience": audience},
                context
            )

            self.state.written_content = result
            self.state.update_stage("writing_completed", result)
            self.state.update_performance(self.name, {
                "success_rate": 1.0,
                "word_count": result.get("word_count", 0),
                "style_adherence": style,
                "audience_appropriateness": audience
            })

            return result

        except Exception as e:
            self.state.log_error(self.name, e, {"style": style, "audience": audience})
            return self._emergency_writing({"analysis_data": analysis_data})

    async def _execute_writing(self, data: dict) -> dict:
        """Execute primary writing operation"""
        analysis_data = data["analysis_data"]
        style = data["style"]
        audience = data["audience"]

        # Simulate writing process based on style
        if style == "detailed":
            await asyncio.sleep(2)
            word_count = 1500
        elif style == "executive":
            await asyncio.sleep(1.5)
            word_count = 800
        else:
            await asyncio.sleep(1)
            word_count = 600

        return {
            "title": "Comprehensive Analysis Report",
            "summary": f"Executive summary of analysis findings for {audience} audience...",
            "sections": [
                "## Executive Summary",
                "## Research Findings",
                "## Analysis and Insights",
                "## Strategic Recommendations",
                "## Conclusion"
            ],
            "content": f"Detailed {style} content for {audience} audience...",
            "word_count": word_count,
            "style": style,
            "audience": audience,
            "confidence_level": analysis_data.get("confidence_score", 0.8),
            "writing_methodology": f"{style}_structured_approach"
        }

    async def _alternative_writing(self, data: dict) -> dict:
        """Alternative writing approach"""
        analysis_data = data["analysis_data"]

        await asyncio.sleep(0.8)

        return {
            "title": "Analysis Summary Report",
            "summary": "Concise summary of key findings...",
            "content": "Alternative writing approach with focus on key points...",
            "word_count": 400,
            "style": "alternative",
            "writing_methodology": "concise_focused",
            "fallback_level": 1
        }

    async def _emergency_writing(self, data: dict) -> dict:
        """Emergency writing - always succeeds"""
        return {
            "title": "Analysis Report",
            "summary": "Report generated with emergency fallback...",
            "content": "Basic content generated to ensure delivery...",
            "word_count": 200,
            "style": "emergency",
            "writing_methodology": "emergency_fallback",
            "fallback_level": 2
        }

class ResearchPipeline:
    """Orchestrates the complete research-analysis-writing pipeline"""

    def __init__(self):
        self.agents = {}
        self.pipeline_strategies = {
            "sequential": self._sequential_pipeline,
            "parallel_research": self._parallel_research_pipeline,
            "adaptive": self._adaptive_pipeline
        }

    async def execute_pipeline(
        self,
        topic: str,
        strategy: str = "sequential",
        requirements: dict | None = None
    ) -> dict:
        """Execute complete research pipeline"""
        workflow_id = f"research_pipeline_{int(asyncio.get_event_loop().time())}"
        state = SharedWorkflowState(workflow_id)

        # Initialize agents with shared state
        self.agents = {
            "research": ResearchAgent(state),
            "analysis": AnalysisAgent(state),
            "writing": WritingAgent(state)
        }

        requirements = requirements or {}

        # Execute pipeline strategy
        strategy_func = self.pipeline_strategies.get(strategy, self._sequential_pipeline)
        result = await strategy_func(topic, requirements, state)

        return {
            "workflow_id": workflow_id,
            "strategy": strategy,
            "topic": topic,
            "final_output": result,
            "workflow_metrics": {
                "stages_completed": list(state.stage_outputs.keys()),
                "total_errors": len(state.error_log),
                "agent_performance": state.agent_performance,
                "success_rate": 1.0 - (len(state.error_log) / max(len(state.stage_outputs), 1))
            },
            "state_snapshot": {
                "research_data": state.research_data,
                "analysis_results": state.analysis_results,
                "written_content": state.written_content
            }
        }

    async def _sequential_pipeline(self, topic: str, requirements: dict, state: SharedWorkflowState) -> dict:
        """Sequential pipeline: research → analysis → writing"""
        # Step 1: Research
        research_data = await self.agents["research"].research(
            topic=topic,
            depth=requirements.get("research_depth", "standard"),
            sources_needed=requirements.get("sources_needed", 5)
        )

        # Step 2: Analysis
        analysis_data = await self.agents["analysis"].analyze(
            research_data=research_data,
            analysis_type=requirements.get("analysis_type", "comprehensive")
        )

        # Step 3: Writing
        final_content = await self.agents["writing"].write(
            analysis_data=analysis_data,
            style=requirements.get("writing_style", "professional"),
            audience=requirements.get("target_audience", "general")
        )

        return final_content

    async def _parallel_research_pipeline(self, topic: str, requirements: dict, state: SharedWorkflowState) -> dict:
        """Parallel research pipeline for multiple angles"""
        # Parallel research on different aspects
        research_tasks = [
            self.agents["research"].research(topic, "standard", 3),
            self.agents["research"].research(f"{topic} trends", "standard", 3),
            self.agents["research"].research(f"{topic} challenges", "standard", 3)
        ]

        # Execute research in parallel
        research_results = await asyncio.gather(*research_tasks, return_exceptions=True)

        # Combine research results
        combined_research = {
            "topic": topic,
            "aspect_research": [
                r if not isinstance(r, Exception) else {"error": str(r)}
                for r in research_results
            ],
            "comprehensive_data": True
        }

        # Analysis and writing (sequential after parallel research)
        analysis_data = await self.agents["analysis"].analyze(combined_research, "comprehensive")
        final_content = await self.agents["writing"].write(analysis_data)

        return final_content

    async def _adaptive_pipeline(self, topic: str, requirements: dict, state: SharedWorkflowState) -> dict:
        """Adaptive pipeline that adjusts based on intermediate results"""
        # Initial research
        research_data = await self.agents["research"].research(topic, "standard", 5)

        # Adaptive analysis based on research quality
        if research_data.get("data_quality") == "high":
            analysis_type = "comprehensive"
        else:
            analysis_type = "basic"

        analysis_data = await self.agents["analysis"].analyze(research_data, analysis_type)

        # Adaptive writing based on analysis confidence
        if analysis_data.get("confidence_score", 0) > 0.8:
            writing_style = "detailed"
        else:
            writing_style = "executive"

        final_content = await self.agents["writing"].write(analysis_data, writing_style)

        return final_content

# Usage examples
async def main():
    pipeline = ResearchPipeline()

    # Sequential pipeline example
    print("=== Sequential Pipeline ===")
    sequential_result = await pipeline.execute_pipeline(
        topic="AI in healthcare",
        strategy="sequential",
        requirements={
            "research_depth": "standard",
            "analysis_type": "comprehensive",
            "writing_style": "professional",
            "target_audience": "healthcare executives"
        }
    )
    print(f"Pipeline completed: {sequential_result['workflow_metrics']['stages_completed']}")
    print(f"Final word count: {sequential_result['final_output']['word_count']}")

    # Parallel research pipeline example
    print("\n=== Parallel Research Pipeline ===")
    parallel_result = await pipeline.execute_pipeline(
        topic="Renewable energy trends",
        strategy="parallel_research",
        requirements={
            "writing_style": "detailed",
            "target_audience": "energy sector professionals"
        }
    )
    print(f"Research aspects: {len(parallel_result['state_snapshot']['research_data'].get('aspect_research', []))}")
    print(f"Total errors: {parallel_result['workflow_metrics']['total_errors']}")

    # Adaptive pipeline example
    print("\n=== Adaptive Pipeline ===")
    adaptive_result = await pipeline.execute_pipeline(
        topic="Quantum computing applications",
        strategy="adaptive",
        requirements={
            "research_depth": "deep",
            "analysis_type": "comprehensive"
        }
    )
    print(f"Success rate: {adaptive_result['workflow_metrics']['success_rate']:.2%}")
    print(f"Analysis confidence: {adaptive_result['final_output']['confidence_level']}")
```

**Cline's Learning Pattern:**

- Identifies multi-stage research and content generation workflows
- Uses SharedWorkflowState for coordinated state management
- Implements different pipeline strategies (sequential, parallel, adaptive)
- Provides comprehensive error handling with fallbacks at each stage
- Includes performance tracking and adaptive decision-making
- Uses proper WorkflowContext for pipeline coordination and monitoring

## Example 2: Data Processing and Quality Assurance Pipeline

**When to Use:** Building a data pipeline that needs validation, processing, and quality checks across multiple stages

**Cline Prompt Example:**

```
I need a data processing pipeline that validates raw data, performs quality checks,
processes it through multiple transformation stages, and generates reports.
Include error handling and quality assurance.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive, TimeoutPrimitive
import asyncio
from typing import Any, Dict, List, Tuple
import json

class DataPipelineState:
    """State management for data processing pipeline"""

    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        self.raw_data: List[dict] = []
        self.validated_data: List[dict] = []
        self.processed_data: List[dict] = []
        self.quality_report: Dict[str, Any] = {}
        self.processing_log: List[dict] = []
        self.quality_metrics: Dict[str, float] = {}
        self.error_summary: List[dict] = []
        self.current_stage = "initialized"
        self.stage_timings: Dict[str, float] = {}
        self.data_lineage: Dict[str, Any] = {}

    def log_processing_stage(self, stage: str, records_processed: int, success: bool, details: dict = None):
        """Log processing stage with metrics"""
        self.processing_log.append({
            "stage": stage,
            "records_processed": records_processed,
            "success": success,
            "details": details or {},
            "timestamp": asyncio.get_event_loop().time()
        })

        if success:
            self.quality_metrics[f"{stage}_success_rate"] = 1.0
        else:
            self.quality_metrics[f"{stage}_success_rate"] = 0.0

    def add_error(self, stage: str, error: Exception, record_id: str = None):
        """Add error to summary"""
        self.error_summary.append({
            "stage": stage,
            "error": str(error),
            "record_id": record_id,
            "timestamp": asyncio.get_event_loop().time()
        })

    def update_stage_timing(self, stage: str, duration: float):
        """Update stage timing"""
        self.stage_timings[stage] = duration
        self.quality_metrics[f"{stage}_avg_time"] = duration

class DataValidationAgent:
    """Agent for data validation and quality checks"""

    def __init__(self, state: DataPipelineState):
        self.state = state
        self.name = "validation_agent"
        self.retry_primitive = RetryPrimitive(
            primitive=self._validate_data,
            max_retries=2,
            backoff_strategy="linear"
        )

    async def validate_dataset(self, raw_data: List[dict], validation_rules: dict = None) -> Tuple[List[dict], Dict[str, Any]]:
        """Validate entire dataset with comprehensive checks"""
        self.state.current_stage = "validating"
        start_time = asyncio.get_event_loop().time()

        validation_rules = validation_rules or {
            "required_fields": ["id", "name", "email"],
            "data_types": {"id": int, "name": str, "email": str},
            "email_pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        }

        validated_records = []
        validation_report = {
            "total_records": len(raw_data),
            "valid_records": 0,
            "invalid_records": 0,
            "validation_errors": [],
            "data_quality_score": 0.0,
            "field_completeness": {},
            "data_type_accuracy": {}
        }

        # Validate each record
        for i, record in enumerate(raw_data):
            try:
                validation_result = await self._validate_single_record(record, validation_rules, i)
                if validation_result["is_valid"]:
                    validated_records.append(validation_result["record"])
                    validation_report["valid_records"] += 1
                else:
                    validation_report["invalid_records"] += 1
                    validation_report["validation_errors"].extend(validation_result["errors"])

            except Exception as e:
                validation_report["invalid_records"] += 1
                self.state.add_error("validation", e, record.get("id", f"index_{i}"))

        # Calculate quality metrics
        validation_report["data_quality_score"] = (
            validation_report["valid_records"] / len(raw_data)
            if raw_data else 0
        )

        validation_report["field_completeness"] = self._calculate_field_completeness(raw_data, validated_records)
        validation_report["data_type_accuracy"] = self._calculate_type_accuracy(raw_data)

        # Update state
        self.state.validated_data = validated_records
        self.state.update_stage_timing("validation", asyncio.get_event_loop().time() - start_time)
        self.state.log_processing_stage(
            "validation",
            len(raw_data),
            validation_report["data_quality_score"] > 0.8,
            validation_report
        )

        return validated_records, validation_report

    async def _validate_single_record(self, record: dict, rules: dict, index: int) -> dict:
        """Validate a single record"""
        errors = []
        cleaned_record = record.copy()

        # Check required fields
        for field in rules["required_fields"]:
            if field not in record or not record[field]:
                errors.append(f"Missing required field: {field}")

        # Check data types
        for field, expected_type in rules["data_types"].items():
            if field in record and not isinstance(record[field], expected_type):
                errors.append(f"Invalid data type for {field}: expected {expected_type.__name__}")

        # Email validation
        if "email" in record and record["email"]:
            import re
            if not re.match(rules["email_pattern"], record["email"]):
                errors.append("Invalid email format")

        # Clean data
        if "name" in cleaned_record:
            cleaned_record["name"] = str(cleaned_record["name"]).strip().title()

        return {
            "is_valid": len(errors) == 0,
            "record": cleaned_record,
            "errors": errors
        }

    def _calculate_field_completeness(self, raw_data: List[dict], validated_data: List[dict]) -> Dict[str, float]:
        """Calculate completeness for each field"""
        if not raw_data:
            return {}

        completeness = {}
        all_fields = set()
        for record in raw_data:
            all_fields.update(record.keys())

        for field in all_fields:
            complete_count = sum(1 for record in raw_data if field in record and record[field])
            completeness[field] = complete_count / len(raw_data)

        return completeness

    def _calculate_type_accuracy(self, raw_data: List[dict]) -> Dict[str, float]:
        """Calculate data type accuracy"""
        if not raw_data:
            return {}

        type_accuracy = {}
        all_fields = set()
        for record in raw_data:
            all_fields.update(record.keys())

        for field in all_fields:
            correct_type_count = 0
            for record in raw_data:
                if field in record and record[field] is not None:
                    # Simple type checking (in real implementation, would be more sophisticated)
                    if isinstance(record[field], (str, int, float, bool)):
                        correct_type_count += 1

            type_accuracy[field] = correct_type_count / len(raw_data)

        return type_accuracy

    async def _validate_data(self, data: dict) -> dict:
        """Validation operation for retry primitive"""
        # This is a placeholder for the actual validation logic
        # In practice, this would contain the core validation algorithm
        return {"validation_result": "success"}

class DataProcessingAgent:
    """Agent for data transformation and processing"""

    def __init__(self, state: DataPipelineState):
        self.state = state
        self.name = "processing_agent"
        self.parallel_processor = ParallelPrimitive([])

    async def process_data(self, validated_data: List[dict], processing_rules: dict = None) -> Tuple[List[dict], Dict[str, Any]]:
        """Process validated data through multiple transformation stages"""
        self.state.current_stage = "processing"
        start_time = asyncio.get_event_loop().time()

        processing_rules = processing_rules or {
            "transformations": ["normalize", "enrich", "aggregate"],
            "batch_size": 100,
            "parallel_processing": True
        }

        processed_records = []
        processing_report = {
            "input_records": len(validated_data),
            "output_records": 0,
            "transformations_applied": processing_rules["transformations"],
            "processing_stages": [],
            "performance_metrics": {}
        }

        # Batch processing
        batch_size = processing_rules["batch_size"]
        batches = [validated_data[i:i + batch_size] for i in range(0, len(validated_data), batch_size)]

        for i, batch in enumerate(batches):
            try:
                batch_result = await self._process_batch(batch, processing_rules)
                processed_records.extend(batch_result)
                processing_report["processing_stages"].append(f"batch_{i}_completed")

            except Exception as e:
                self.state.add_error("processing", e, f"batch_{i}")
                # Continue with next batch

        processing_report["output_records"] = len(processed_records)
        processing_report["success_rate"] = len(processed_records) / len(validated_data) if validated_data else 0

        # Update state
        self.state.processed_data = processed_records
        self.state.update_stage_timing("processing", asyncio.get_event_loop().time() - start_time)
        self.state.log_processing_stage(
            "processing",
            len(validated_data),
            processing_report["success_rate"] > 0.9,
            processing_report
        )

        return processed_records, processing_report

    async def _process_batch(self, batch: List[dict], rules: dict) -> List[dict]:
        """Process a batch of records"""
        processed_batch = []

        for record in batch:
            try:
                processed_record = await self._transform_record(record, rules)
                processed_batch.append(processed_record)
            except Exception as e:
                self.state.add_error("record_processing", e, record.get("id"))
                # Continue with next record

        return processed_batch

    async def _transform_record(self, record: dict, rules: dict) -> dict:
        """Transform individual record"""
        transformed = record.copy()

        # Apply transformations
        for transformation in rules["transformations"]:
            if transformation == "normalize":
                transformed = await self._normalize_record(transformed)
            elif transformation == "enrich":
                transformed = await self._enrich_record(transformed)
            elif transformation == "aggregate":
                transformed = await self._aggregate_record(transformed)

        return transformed

    async def _normalize_record(self, record: dict) -> dict:
        """Normalize record data"""
        normalized = record.copy()

        # Normalize text fields
        for key, value in record.items():
            if isinstance(value, str):
                normalized[key] = value.strip().lower()

        return normalized

    async def _enrich_record(self, record: dict) -> dict:
        """Enrich record with additional data"""
        enriched = record.copy()

        # Add processing timestamp
        enriched["processed_at"] = asyncio.get_event_loop().time()
        enriched["data_source"] = "validated_dataset"

        return enriched

    async def _aggregate_record(self, record: dict) -> dict:
        """Aggregate record metrics"""
        aggregated = record.copy()

        # Add aggregation metadata
        aggregated["record_length"] = len(str(record))
        aggregated["field_count"] = len(record)

        return aggregated

class QualityAssuranceAgent:
    """Agent for quality assurance and reporting"""

    def __init__(self, state: DataPipelineState):
        self.state = state
        self.name = "qa_agent"
        self.fallback_reporting = FallbackPrimitive(
            primary=self._generate_comprehensive_report,
            fallbacks=[self._generate_basic_report, self._generate_minimal_report]
        )

    async def perform_quality_assurance(self, processed_data: List[dict], reports: List[dict]) -> Dict[str, Any]:
        """Perform comprehensive quality assurance"""
        self.state.current_stage = "quality_assurance"
        start_time = asyncio.get_event_loop().time()

        try:
            qa_report = await self.fallback_reporting.execute(
                {"processed_data": processed_data, "reports": reports},
                WorkflowContext(workflow_id=self.state.pipeline_id)
            )

            # Update state
            self.state.quality_report = qa_report
            self.state.update_stage_timing("quality_assurance", asyncio.get_event_loop().time() - start_time)
            self.state.log_processing_stage(
                "quality_assurance",
                len(processed_data),
                qa_report.get("overall_quality_score", 0) > 0.8,
                qa_report
            )

            return qa_report

        except Exception as e:
            self.state.add_error("quality_assurance", e)
            return self._generate_minimal_report({"processed_data": processed_data, "reports": reports})

    async def _generate_comprehensive_report(self, data: dict) -> dict:
        """Generate comprehensive quality report"""
        processed_data = data["processed_data"]
        reports = data["reports"]

        await asyncio.sleep(1)  # Simulate report generation

        return {
            "report_type": "comprehensive",
            "overall_quality_score": 0.92,
            "data_completeness": 0.95,
            "data_accuracy": 0.88,
            "processing_efficiency": 0.91,
            "recommendations": [
                "Data quality is excellent",
                "Consider additional validation for email fields",
                "Processing performance is optimal"
            ],
            "detailed_metrics": {
                "total_records": len(processed_data),
                "validation_success_rate": 0.95,
                "processing_success_rate": 0.98,
                "average_processing_time": 0.15
            },
            "compliance_check": {
                "gdpr_compliant": True,
                "data_anonymization": "complete",
                "audit_trail": "comprehensive"
            }
        }

    async def _generate_basic_report(self, data: dict) -> dict:
        """Generate basic quality report"""
        processed_data = data["processed_data"]

        await asyncio.sleep(0.5)

        return {
            "report_type": "basic",
            "overall_quality_score": 0.75,
            "data_completeness": 0.80,
            "data_accuracy": 0.70,
            "processing_efficiency": 0.75,
            "recommendations": [
                "Data quality is acceptable",
                "Consider additional validation steps"
            ],
            "summary": f"Processed {len(processed_data)} records with basic quality checks"
        }

    async def _generate_minimal_report(self, data: dict) -> dict:
        """Generate minimal quality report (fallback)"""
        processed_data = data["processed_data"]

        return {
            "report_type": "minimal",
            "overall_quality_score": 0.50,
            "summary": f"Processed {len(processed_data)} records",
            "note": "Minimal quality report generated due to system constraints"
        }

class DataProcessingPipeline:
    """Orchestrates the complete data processing pipeline"""

    def __init__(self):
        self.pipeline_strategies = {
            "standard": self._standard_pipeline,
            "parallel": self._parallel_pipeline,
            "robust": self._robust_pipeline
        }

    async def execute_pipeline(
        self,
        raw_data: List[dict],
        strategy: str = "standard",
        config: dict | None = None
    ) -> dict:
        """Execute complete data processing pipeline"""
        pipeline_id = f"data_pipeline_{int(asyncio.get_event_loop().time())}"
        state = DataPipelineState(pipeline_id)
        state.raw_data = raw_data

        config = config or {}

        # Initialize agents
        agents = {
            "validation": DataValidationAgent(state),
            "processing": DataProcessingAgent(state),
            "quality_assurance": QualityAssuranceAgent(state)
        }

        # Execute pipeline strategy
        strategy_func = self.pipeline_strategies.get(strategy, self._standard_pipeline)
        result = await strategy_func(raw_data, agents, config)

        return {
            "pipeline_id": pipeline_id,
            "strategy": strategy,
            "input_records": len(raw_data),
            "output_records": len(state.processed_data),
            "final_report": state.quality_report,
            "pipeline_metrics": {
                "stages_completed": list(state.stage_timings.keys()),
                "total_errors": len(state.error_summary),
                "overall_success_rate": 1.0 - (len(state.error_summary) / max(len(state.processing_log), 1)),
                "processing_log": state.processing_log
            },
            "quality_metrics": state.quality_metrics
        }

    async def _standard_pipeline(self, raw_data: List[dict], agents: dict, config: dict) -> dict:
        """Standard sequential pipeline"""
        # Validation
        validated_data, validation_report = await agents["validation"].validate_dataset(
            raw_data, config.get("validation_rules")
        )

        # Processing
        processed_data, processing_report = await agents["processing"].process_data(
            validated_data, config.get("processing_rules")
        )

        # Quality Assurance
        qa_report = await agents["quality_assurance"].perform_quality_assurance(
            processed_data, [validation_report, processing_report]
        )

        return {
            "validation_report": validation_report,
            "processing_report": processing_report,
            "qa_report": qa_report
        }

    async def _parallel_pipeline(self, raw_data: List[dict], agents: dict, config: dict) -> dict:
        """Parallel processing pipeline"""
        # Validation and initial processing in parallel
        validation_task = agents["validation"].validate_dataset(raw_data)
        processing_task = agents["processing"].process_data(raw_data)  # Process raw data initially

        validation_result, processing_result = await asyncio.gather(
            validation_task,
            processing_task,
            return_exceptions=True
        )

        # Combine results
        if not isinstance(validation_result, Exception):
            validated_data, validation_report = validation_result
        else:
            validated_data, validation_report = [], {"error": str(validation_result)}

        if not isinstance(processing_result, Exception):
            processed_data, processing_report = processing_result
        else:
            processed_data, processing_report = [], {"error": str(processing_result)}

        # Quality Assurance
        qa_report = await agents["quality_assurance"].perform_quality_assurance(
            processed_data, [validation_report, processing_report]
        )

        return {
            "validation_report": validation_report,
            "processing_report": processing_report,
            "qa_report": qa_report
        }

    async def _robust_pipeline(self, raw_data: List[dict], agents: dict, config: dict) -> dict:
        """Robust pipeline with comprehensive error handling"""
        try:
            # Validation with timeout
            validated_data, validation_report = await asyncio.wait_for(
                agents["validation"].validate_dataset(raw_data, config.get("validation_rules")),
                timeout=30.0
            )

            # Processing with timeout
            processed_data, processing_report = await asyncio.wait_for(
                agents["processing"].process_data(validated_data, config.get("processing_rules")),
                timeout=60.0
            )

            # Quality Assurance
            qa_report = await agents["quality_assurance"].perform_quality_assurance(
                processed_data, [validation_report, processing_report]
            )

            return {
                "validation_report": validation_report,
                "processing_report": processing_report,
                "qa_report": qa_report
            }

        except asyncio.TimeoutError:
            return {
                "error": "Pipeline timeout",
                "partial_results": {
                    "validation_completed": "validation" in agents["validation"].state.stage_timings,
                    "processing_completed": "processing" in agents["processing"].state.stage_timings
                }
            }

# Usage examples
async def main():
    pipeline = DataProcessingPipeline()

    # Sample data
    sample_data = [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25},
        {"id": 3, "name": "", "email": "invalid-email", "age": "thirty"},  # Invalid record
        {"id": 4, "name": "Bob Johnson", "email": "bob@example.com", "age": 35}
    ]

    # Standard pipeline
    print("=== Standard Pipeline ===")
    standard_result = await pipeline.execute_pipeline(
        sample_data,
        strategy="standard",
        config={
            "validation_rules": {
                "required_fields": ["id", "name", "email"],
                "data_types": {"id": int, "name": str, "email": str, "age": int}
            }
        }
    )
    print(f"Input records: {standard_result['input_records']}")
    print(f"Output records: {standard_result['output_records']}")
    print(f"Quality score: {standard_result['final_report']['overall_quality_score']}")

    # Robust pipeline
    print("\n=== Robust Pipeline ===")
    robust_result = await pipeline.execute_pipeline(
        sample_data,
        strategy="robust"
    )
    print(f"Success rate: {standard_result['pipeline_metrics']['overall_success_rate']:.2%}")
    print(f"Total errors: {standard_result['pipeline_metrics']['total_errors']}")
```

**Cline's Learning Pattern:**

- Identifies complex data processing and quality assurance workflows
- Uses DataPipelineState for comprehensive state management across pipeline stages
- Implements different pipeline strategies (standard, parallel, robust)
- Provides comprehensive error handling and fallback reporting
- Includes performance monitoring and quality metrics collection
- Uses proper WorkflowContext for pipeline coordination and tracking

## Cline Detection Patterns

**Data Pipeline Indicators:**

- "data processing pipeline"
- "data validation and quality checks"
- "multiple transformation stages"
- "batch processing"
- "data quality assurance"
- "pipeline orchestration"
- "ETL process"
- "data lineage tracking"

**Cline's Response Strategy:**

1. Identify data processing and validation requirements
2. Suggest DataPipelineState for comprehensive state management
3. Recommend appropriate pipeline strategies based on requirements
4. Implement validation agents with comprehensive error handling
5. Use proper WorkflowContext for pipeline coordination and monitoring

## Common Mistakes to Avoid

❌ **Wrong:** No state management between pipeline stages

```python
# Data gets lost between stages
validated_data = await validate(raw_data)
processed_data = await process(validated_data)  # Can't access validation results!
```

✅ **Right:** Comprehensive state management

```python
# Shared state across all stages
state = DataPipelineState(pipeline_id)
state.validated_data = validated_data
state.processed_data = processed_data
```

❌ **Wrong:** No quality assurance

```python
# Process data without quality checks
processed_data = await process(raw_data)
return processed_data  # No quality validation!
```

✅ **Right:** Comprehensive quality assurance

```python
# Multi-stage quality assurance
qa_agent = QualityAssuranceAgent(state)
qa_report = await qa_agent.perform_quality_assurance(processed_data, reports)
```

❌ **Wrong:** No error recovery

```python
# Single point of failure
if validation_fails:
    return {"error": "Pipeline failed"}  # No recovery!
```

✅ **Right:** Robust error handling and fallbacks

```python
# Multiple fallback strategies
fallback_reporting = FallbackPrimitive(
    primary=comprehensive_report,
    fallbacks=[basic_report, minimal_report]
)
```

---

**Next Steps:** When cline detects complex data processing and quality assurance scenarios, it should automatically suggest appropriate pipeline architectures, state management strategies, and quality assurance patterns based on the specific data requirements and use cases.


---
**Logseq:** [[TTA.dev/.cline/Examples/Workflows/Agent_coordination_patterns]]
