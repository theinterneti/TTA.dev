# ParallelPrimitive Examples for Cline

**Purpose:** Learn how to implement parallel execution with TTA.dev's ParallelPrimitive for concurrent processing and improved performance

## Example 1: Concurrent LLM Calls for Faster Responses

**When to Use:** You need to call multiple LLM services simultaneously to get faster responses or compare outputs

**Cline Prompt Example:**

```
I have multiple LLM services (GPT-4, Claude, and Gemini) and want to call them in parallel
to get the fastest response or compare their outputs.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio

class ConcurrentLLMService:
    def __init__(self):
        # Create LLM call primitives
        self.gpt4_call = self._create_llm_primitive("gpt-4", self._call_gpt4)
        self.claude_call = self._create_llm_primitive("claude", self._call_claude)
        self.gemini_call = self._create_llm_primitive("gemini", self._call_gemini)

        # Parallel execution for fastest response
        self.fastest_response = ParallelPrimitive([
            self.gpt4_call,
            self.claude_call,
            self.gemini_call
        ])

        # Use | operator for cleaner syntax
        self.all_responses = self.gpt4_call | self.claude_call | self.gemini_call

    async def get_fastest_response(self, prompt: str) -> dict:
        """Get response from the fastest LLM provider"""
        context = WorkflowContext(
            workflow_id="fastest-llm",
            metadata={
                "prompt_length": len(prompt),
                "providers": ["gpt-4", "claude", "gemini"]
            }
        )

        try:
            # Execute all LLMs in parallel
            responses = await self.fastest_response.execute(prompt, context)

            # Find fastest response (responses are ordered)
            fastest_idx = 0
            fastest_time = float('inf')

            for i, response in enumerate(responses):
                if response.get("response_time", 0) < fastest_time:
                    fastest_time = response.get("response_time", 0)
                    fastest_idx = i

            fastest_response = responses[fastest_idx]
            fastest_response["was_fastest"] = True
            fastest_response["all_responses"] = responses

            return fastest_response

        except Exception as e:
            return {
                "error": "All LLM calls failed",
                "fallback": True,
                "error_details": str(e)
            }

    async def compare_all_responses(self, prompt: str) -> dict:
        """Get responses from all LLM providers for comparison"""
        context = WorkflowContext(
            workflow_id="llm-comparison",
            metadata={
                "prompt_length": len(prompt),
                "comparison_mode": True
            }
        )

        try:
            responses = await self.all_responses.execute(prompt, context)

            return {
                "comparison_results": responses,
                "total_providers": len(responses),
                "responses_available": [r.get("provider") for r in responses if "provider" in r]
            }

        except Exception as e:
            return {
                "error": "LLM comparison failed",
                "error_details": str(e)
            }

    def _create_llm_primitive(self, provider_name: str, llm_func):
        """Create a wrapped LLM primitive with metadata"""

        class LLMPrimitive:
            def __init__(self, provider: str, func):
                self.provider = provider
                self.func = func

            async def execute(self, prompt: str, context: WorkflowContext) -> dict:
                start_time = asyncio.get_event_loop().time()

                try:
                    result = await self.func(prompt)
                    end_time = asyncio.get_event_loop().time()

                    return {
                        "provider": self.provider,
                        "response": result,
                        "response_time": end_time - start_time,
                        "success": True
                    }
                except Exception as e:
                    return {
                        "provider": self.provider,
                        "error": str(e),
                        "response_time": asyncio.get_event_loop().time() - start_time,
                        "success": False
                    }

        return LLMPrimitive(provider_name, llm_func)

    async def _call_gpt4(self, prompt: str) -> str:
        # Simulate GPT-4 API call
        await asyncio.sleep(2)  # Simulate 2-second response
        return f"GPT-4 response to: {prompt[:50]}..."

    async def _call_claude(self, prompt: str) -> str:
        # Simulate Claude API call
        await asyncio.sleep(1.5)  # Simulate 1.5-second response
        return f"Claude response to: {prompt[:50]}..."

    async def _call_gemini(self, prompt: str) -> str:
        # Simulate Gemini API call
        await asyncio.sleep(3)  # Simulate 3-second response
        return f"Gemini response to: {prompt[:50]}..."

# Usage examples
async def main():
    llm_service = ConcurrentLLMService()

    # Get fastest response
    fastest = await llm_service.get_fastest_response("What is the weather?")
    print(f"Fastest response: {fastest['provider']} in {fastest['response_time']:.2f}s")

    # Compare all responses
    comparison = await llm_service.compare_all_responses("Explain quantum computing")
    for response in comparison["comparison_results"]:
        print(f"{response['provider']}: {response['response'][:30]}...")
```

**Cline's Learning Pattern:**

- Identifies multiple API calls that can run in parallel
- Uses ParallelPrimitive with the `|` operator for clean syntax
- Implements response time comparison for optimization
- Provides fallback strategies for failed calls
- Proper WorkflowContext for tracing parallel execution

## Example 2: Multiple API Aggregations

**When to Use:** You need to gather data from multiple external APIs and combine the results

**Cline Prompt Example:**

```
I need to fetch data from multiple APIs (weather, news, stock prices) and combine them
into a single dashboard. Make the API calls parallel for better performance.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import aiohttp
import asyncio

class APIDataAggregator:
    def __init__(self):
        # Create API fetching primitives
        self.weather_api = self._create_api_primitive("weather", self._fetch_weather)
        self.news_api = self._create_api_primitive("news", self._fetch_news)
        self.stock_api = self._create_api_primitive("stocks", self._fetch_stock_data)

        # Parallel execution for all APIs
        self.parallel_apis = ParallelPrimitive([
            self.weather_api,
            self.news_api,
            self.stock_api
        ])

    async def get_dashboard_data(self, location: str, stocks: list[str]) -> dict:
        """Get all dashboard data in parallel"""
        context = WorkflowContext(
            workflow_id="dashboard-aggregation",
            metadata={
                "location": location,
                "stock_count": len(stocks),
                "api_count": 3
            }
        )

        try:
            # Execute all API calls in parallel
            results = await self.parallel_apis.execute(
                {"location": location, "stocks": stocks},
                context
            )

            # Combine results into dashboard format
            dashboard_data = {
                "weather": None,
                "news": None,
                "stocks": None,
                "aggregation_success": True,
                "total_apis_called": len(results)
            }

            for result in results:
                if result.get("success"):
                    if result["api_type"] == "weather":
                        dashboard_data["weather"] = result["data"]
                    elif result["api_type"] == "news":
                        dashboard_data["news"] = result["data"]
                    elif result["api_type"] == "stocks":
                        dashboard_data["stocks"] = result["data"]

            # Check if we got all required data
            missing_apis = []
            for api_type in ["weather", "news", "stocks"]:
                if dashboard_data[api_type] is None:
                    missing_apis.append(api_type)

            if missing_apis:
                dashboard_data["warning"] = f"Missing data from: {missing_apis}"
                dashboard_data["partial_success"] = True

            return dashboard_data

        except Exception as e:
            return {
                "error": "API aggregation failed",
                "error_details": str(e),
                "aggregation_success": False
            }

    async def get_essential_data(self, location: str) -> dict:
        """Get only essential data (weather + news) in parallel"""
        context = WorkflowContext(
            workflow_id="essential-data",
            metadata={"location": location, "essential_apis": True}
        )

        # Only call essential APIs
        essential_apis = ParallelPrimitive([self.weather_api, self.news_api])

        try:
            results = await essential_apis.execute({"location": location}, context)

            return {
                "weather": next((r["data"] for r in results if r["api_type"] == "weather"), None),
                "news": next((r["data"] for r in results if r["api_type"] == "news"), None),
                "essential_success": True
            }

        except Exception as e:
            return {
                "error": "Essential data fetch failed",
                "error_details": str(e)
            }

    def _create_api_primitive(self, api_type: str, api_func):
        """Create a wrapped API primitive with error handling"""

        class APIPrimitive:
            def __init__(self, api_type: str, func):
                self.api_type = api_type
                self.func = func

            async def execute(self, data: dict, context: WorkflowContext) -> dict:
                try:
                    result = await self.func(data)
                    return {
                        "api_type": self.api_type,
                        "data": result,
                        "success": True
                    }
                except Exception as e:
                    return {
                        "api_type": self.api_type,
                        "error": str(e),
                        "success": False
                    }

        return APIPrimitive(api_type, api_func)

    async def _fetch_weather(self, data: dict) -> dict:
        # Simulate weather API call
        await asyncio.sleep(0.5)
        location = data.get("location", "Unknown")
        return {
            "location": location,
            "temperature": 22,
            "condition": "Sunny",
            "humidity": 65
        }

    async def _fetch_news(self, data: dict) -> dict:
        # Simulate news API call
        await asyncio.sleep(0.3)
        return {
            "headlines": [
                "Tech stocks rally on AI optimism",
                "Climate summit reaches new agreements",
                "Local economy shows strong growth"
            ],
            "timestamp": "2025-11-08T13:55:00Z"
        }

    async def _fetch_stock_data(self, data: dict) -> dict:
        # Simulate stock API call
        await asyncio.sleep(0.4)
        stocks = data.get("stocks", ["AAPL", "GOOGL"])
        return {
            "stocks": {symbol: {"price": 150.25, "change": "+2.1%"} for symbol in stocks},
            "market_status": "open"
        }

# Usage example
async def main():
    aggregator = APIDataAggregator()

    # Get full dashboard data
    dashboard = await aggregator.get_dashboard_data("New York", ["AAPL", "GOOGL", "MSFT"])
    print(f"Dashboard: {dashboard['total_apis_called']} APIs called")

    # Get essential data only
    essential = await aggregator.get_essential_data("San Francisco")
    print(f"Essential data retrieved: {essential['essential_success']}")
```

**Cline's Learning Pattern:**

- Identifies multiple external API calls that can be parallelized
- Uses ParallelPrimitive to execute API calls concurrently
- Implements result aggregation and error handling
- Provides selective API calling based on requirements
- Proper context tracking for API aggregation workflows

## Example 3: Parallel Data Processing Pipelines

**When to Use:** You have large datasets that need to be processed through multiple transformation pipelines

**Cline Prompt Example:**

```
I have a large dataset that needs multiple processing steps: data cleaning, feature extraction,
validation, and enrichment. Process these steps in parallel to speed up the pipeline.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio
import json

class DataProcessingPipeline:
    def __init__(self):
        # Create data processing primitives
        self.data_cleaner = self._create_processor("cleaner", self._clean_data)
        self.feature_extractor = self._create_processor("extractor", self._extract_features)
        self.data_validator = self._create_processor("validator", self._validate_data)
        self.data_enricher = self._create_processor("enricher", self._enrich_data)

        # Parallel processing pipeline
        self.parallel_pipeline = ParallelPrimitive([
            self.data_cleaner,
            self.feature_extractor,
            self.data_validator,
            self.data_enricher
        ])

    async def process_dataset(self, raw_data: list[dict]) -> dict:
        """Process entire dataset through parallel pipeline"""
        context = WorkflowContext(
            workflow_id="data-pipeline",
            metadata={
                "record_count": len(raw_data),
                "processing_steps": 4
            }
        )

        try:
            # Process all data in parallel
            results = await self.parallel_pipeline.execute(raw_data, context)

            # Combine results from all processing steps
            processed_data = {
                "cleaned_data": None,
                "features": None,
                "validation_report": None,
                "enriched_data": None,
                "processing_summary": {}
            }

            for result in results:
                if result.get("success"):
                    step_name = result["step"]
                    processed_data[step_name] = result["data"]
                    processed_data["processing_summary"][step_name] = "success"
                else:
                    step_name = result["step"]
                    processed_data["processing_summary"][step_name] = f"failed: {result['error']}"

            # Calculate processing statistics
            successful_steps = sum(1 for status in processed_data["processing_summary"].values() if status == "success")
            processed_data["processing_stats"] = {
                "total_steps": 4,
                "successful_steps": successful_steps,
                "success_rate": successful_steps / 4,
                "processed_records": len(raw_data)
            }

            return processed_data

        except Exception as e:
            return {
                "error": "Pipeline processing failed",
                "error_details": str(e),
                "raw_data_count": len(raw_data)
            }

    async def quick_validation(self, data_sample: list[dict]) -> dict:
        """Run only validation and cleaning in parallel for quick checks"""
        context = WorkflowContext(
            workflow_id="quick-validation",
            metadata={"sample_size": len(data_sample), "validation_only": True}
        )

        # Only run essential processing steps
        quick_pipeline = ParallelPrimitive([self.data_cleaner, self.data_validator])

        try:
            results = await quick_pipeline.execute(data_sample, context)

            return {
                "cleaned_sample": None,
                "validation_report": None,
                "quick_processing_success": True,
                "steps_completed": len(results)
            }

        except Exception as e:
            return {
                "error": "Quick validation failed",
                "error_details": str(e)
            }

    def _create_processor(self, step_name: str, process_func):
        """Create a wrapped data processing primitive"""

        class DataProcessor:
            def __init__(self, step: str, func):
                self.step = step
                self.func = func

            async def execute(self, data: list[dict], context: WorkflowContext) -> dict:
                try:
                    result = await self.func(data)
                    return {
                        "step": self.step,
                        "data": result,
                        "success": True,
                        "records_processed": len(data)
                    }
                except Exception as e:
                    return {
                        "step": self.step,
                        "error": str(e),
                        "success": False
                    }

        return DataProcessor(step_name, process_func)

    async def _clean_data(self, data: list[dict]) -> list[dict]:
        # Simulate data cleaning process
        await asyncio.sleep(1)  # Simulate processing time
        cleaned = []
        for record in data:
            # Remove empty fields, standardize formats
            cleaned_record = {k: v for k, v in record.items() if v is not None}
            cleaned.append(cleaned_record)
        return cleaned

    async def _extract_features(self, data: list[dict]) -> dict:
        # Simulate feature extraction
        await asyncio.sleep(1.2)
        return {
            "total_records": len(data),
            "feature_count": len(data[0].keys()) if data else 0,
            "data_types": {k: type(v).__name__ for k, v in data[0].items()} if data else {},
            "feature_matrix_shape": (len(data), len(data[0]) if data else 0)
        }

    async def _validate_data(self, data: list[dict]) -> dict:
        # Simulate data validation
        await asyncio.sleep(0.8)
        validation_results = {
            "total_records": len(data),
            "valid_records": 0,
            "invalid_records": 0,
            "validation_errors": []
        }

        for i, record in enumerate(data):
            # Check for required fields
            if not all(record.get(field) for field in ["id", "name"]):
                validation_results["invalid_records"] += 1
                validation_results["validation_errors"].append(f"Record {i}: missing required fields")
            else:
                validation_results["valid_records"] += 1

        validation_results["validation_rate"] = validation_results["valid_records"] / len(data) if data else 0
        return validation_results

    async def _enrich_data(self, data: list[dict]) -> list[dict]:
        # Simulate data enrichment
        await asyncio.sleep(1.5)
        enriched = []
        for record in data:
            # Add enriched fields
            enriched_record = record.copy()
            enriched_record.update({
                "processed_at": "2025-11-08T13:55:00Z",
                "data_quality_score": 0.95,
                "enrichment_applied": True
            })
            enriched.append(enriched_record)
        return enriched

# Usage example
async def main():
    pipeline = DataProcessingPipeline()

    # Sample data
    sample_data = [
        {"id": 1, "name": "John", "age": 30, "email": "john@example.com"},
        {"id": 2, "name": "Jane", "age": 25, "email": "jane@example.com"},
        {"id": 3, "name": "Bob", "age": None, "email": "bob@example.com"}
    ]

    # Process full dataset
    results = await pipeline.process_dataset(sample_data)
    print(f"Processing success rate: {results['processing_stats']['success_rate']}")

    # Quick validation
    quick_results = await pipeline.quick_validation(sample_data)
    print(f"Quick validation completed: {quick_results['quick_processing_success']}")
```

**Cline's Learning Pattern:**

- Identifies data processing workflows that can be parallelized
- Uses ParallelPrimitive for concurrent data processing steps
- Implements comprehensive result aggregation and error handling
- Provides selective processing for different use cases
- Proper context tracking for data pipeline monitoring

## Example 4: Multi-Provider Comparisons

**When to Use:** You need to compare results from different service providers to choose the best option

**Cline Prompt Example:**

```
I want to compare translation services from Google, AWS, and Azure to see which one
provides the best quality for my content. Run them in parallel for efficiency.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio
import time

class TranslationComparisonService:
    def __init__(self):
        # Create translation service primitives
        self.google_translate = self._create_translator("google", self._google_translate)
        self.aws_translate = self._create_translator("aws", self._aws_translate)
        self.azure_translate = self._create_translator("azure", self._azure_translate)

        # Parallel comparison
        self.comparison_pipeline = ParallelPrimitive([
            self.google_translate,
            self.aws_translate,
            self.azure_translate
        ])

    async def compare_translation_quality(self, text: str, target_language: str) -> dict:
        """Compare translation quality across all providers"""
        context = WorkflowContext(
            workflow_id="translation-comparison",
            metadata={
                "text_length": len(text),
                "target_language": target_language,
                "providers": ["google", "aws", "azure"]
            }
        )

        try:
            # Execute all translations in parallel
            start_time = time.time()
            results = await self.comparison_pipeline.execute(
                {"text": text, "target_language": target_language},
                context
            )
            total_time = time.time() - start_time

            # Analyze results
            translation_results = []
            successful_translations = 0

            for result in results:
                if result.get("success"):
                    successful_translations += 1
                    translation_result = {
                        "provider": result["provider"],
                        "translation": result["translation"],
                        "confidence": result.get("confidence", 0.0),
                        "cost": result.get("cost", 0.0),
                        "processing_time": result.get("processing_time", 0.0)
                    }
                    translation_results.append(translation_result)

            # Determine best translation
            best_translation = None
            if translation_results:
                # Choose based on confidence score (could be more sophisticated)
                best_translation = max(
                    translation_results,
                    key=lambda x: x["confidence"]
                )

            return {
                "comparison_results": translation_results,
                "best_translation": best_translation,
                "total_providers": len(results),
                "successful_providers": successful_translations,
                "total_comparison_time": total_time,
                "recommendation": {
                    "provider": best_translation["provider"] if best_translation else None,
                    "reason": "highest confidence score" if best_translation else "no successful translations"
                }
            }

        except Exception as e:
            return {
                "error": "Translation comparison failed",
                "error_details": str(e)
            }

    async def fast_translation(self, text: str, target_language: str) -> dict:
        """Get translation from the fastest available provider"""
        context = WorkflowContext(
            workflow_id="fast-translation",
            metadata={"text_length": len(text), "target_language": target_language}
        )

        try:
            results = await self.comparison_pipeline.execute(
                {"text": text, "target_language": target_language},
                context
            )

            # Find fastest successful translation
            fastest_translation = None
            fastest_time = float('inf')

            for result in results:
                if result.get("success") and result.get("processing_time", 0) < fastest_time:
                    fastest_time = result.get("processing_time", 0)
                    fastest_translation = {
                        "provider": result["provider"],
                        "translation": result["translation"],
                        "processing_time": fastest_time
                    }

            if fastest_translation:
                return {
                    "fastest_translation": fastest_translation,
                    "success": True
                }
            else:
                return {
                    "error": "No successful translations available",
                    "success": False
                }

        except Exception as e:
            return {
                "error": "Fast translation failed",
                "error_details": str(e),
                "success": False
            }

    def _create_translator(self, provider_name: str, translate_func):
        """Create a wrapped translation service primitive"""

        class TranslationService:
            def __init__(self, provider: str, func):
                self.provider = provider
                self.func = func

            async def execute(self, data: dict, context: WorkflowContext) -> dict:
                start_time = time.time()

                try:
                    result = await self.func(data)
                    processing_time = time.time() - start_time

                    return {
                        "provider": self.provider,
                        "translation": result,
                        "success": True,
                        "processing_time": processing_time,
                        "confidence": self._calculate_confidence(self.provider),
                        "cost": self._calculate_cost(self.provider, len(data["text"]))
                    }

                except Exception as e:
                    processing_time = time.time() - start_time
                    return {
                        "provider": self.provider,
                        "error": str(e),
                        "success": False,
                        "processing_time": processing_time
                    }

            def _calculate_confidence(self, provider: str) -> float:
                # Simulate different confidence levels
                confidence_map = {
                    "google": 0.92,
                    "aws": 0.88,
                    "azure": 0.85
                }
                return confidence_map.get(provider, 0.8)

            def _calculate_cost(self, provider: str, text_length: int) -> float:
                # Simulate different cost structures
                cost_map = {
                    "google": 0.00002 * text_length,
                    "aws": 0.000015 * text_length,
                    "azure": 0.000018 * text_length
                }
                return cost_map.get(provider, 0.00002 * text_length)

        return TranslationService(provider_name, translate_func)

    async def _google_translate(self, data: dict) -> str:
        # Simulate Google Translate API call
        await asyncio.sleep(1.2)  # Simulate processing time
        text = data["text"]
        target = data["target_language"]
        return f"Google translation: '{text}' → {target}"

    async def _aws_translate(self, data: dict) -> str:
        # Simulate AWS Translate API call
        await asyncio.sleep(1.0)  # Simulate processing time
        text = data["text"]
        target = data["target_language"]
        return f"AWS translation: '{text}' → {target}"

    async def _azure_translate(self, data: dict) -> str:
        # Simulate Azure Translator API call
        await asyncio.sleep(1.5)  # Simulate processing time
        text = data["text"]
        target = data["target_language"]
        return f"Azure translation: '{text}' → {target}"

# Usage example
async def main():
    translation_service = TranslationComparisonService()

    # Compare translation quality
    comparison = await translation_service.compare_translation_quality(
        "Hello, how are you today?",
        "es"
    )
    print(f"Best provider: {comparison['recommendation']['provider']}")

    # Get fastest translation
    fast_result = await translation_service.fast_translation(
        "Good morning!",
        "fr"
    )
    if fast_result["success"]:
        print(f"Fastest: {fast_result['fastest_translation']['provider']}")
```

**Cline's Learning Pattern:**

- Identifies comparison scenarios across multiple providers
- Uses ParallelPrimitive to execute provider calls concurrently
- Implements quality analysis and recommendation logic
- Provides both quality and speed-based selection strategies
- Proper cost and confidence tracking for informed decisions

## Cline Detection Patterns

**ParallelPrimitive Indicators:**

- "call multiple APIs in parallel"
- "process concurrently"
- "run simultaneously"
- "compare different providers"
- "parallel processing"
- "concurrent execution"
- "faster by running in parallel"
- "aggregate data from multiple sources"

**Cline's Response Strategy:**

1. Identify independent operations that can run in parallel
2. Use ParallelPrimitive with the `|` operator for clean syntax
3. Implement result aggregation and comparison logic
4. Add error handling for partial failures
5. Use proper WorkflowContext for parallel execution tracing

## Common Mistakes to Avoid

❌ **Wrong:** Sequential processing when parallel is possible

```python
# Sequential - slow
result1 = await api1.call()
result2 = await api2.call()
result3 = await api3.call()
```

✅ **Right:** Parallel processing

```python
# Parallel - fast
parallel_apis = api1 | api2 | api3
results = await parallel_apis.execute(data, context)
```

❌ **Wrong:** No error handling for parallel execution

```python
# If one fails, all might fail
results = await ParallelPrimitive([api1, api2, api3]).execute(data, context)
```

✅ **Right:** Handle partial failures

```python
# Handle individual failures
results = await ParallelPrimitive([api1, api2, api3]).execute(data, context)
successful = [r for r in results if r.get("success")]
```

❌ **Wrong:** Not using the `|` operator for clean composition

```python
# Verbose
parallel_apis = ParallelPrimitive([api1, api2, api3])
```

✅ **Right:** Use the `|` operator

```python
# Clean
parallel_apis = api1 | api2 | api3
```

---

**Next Steps:** When cline detects parallelizable operations, it should automatically suggest ParallelPrimitive with the `|` operator for clean syntax and provide aggregation/comparison strategies based on the use case.


---
**Logseq:** [[TTA.dev/.cline/Examples/Primitives/Parallel_primitive]]
