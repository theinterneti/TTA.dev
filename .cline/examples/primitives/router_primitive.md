# RouterPrimitive Examples for Cline

**Purpose:** Learn how to implement intelligent routing with TTA.dev's RouterPrimitive for optimal resource allocation and cost optimization

## Example 1: Intelligent Request Routing

**When to Use:** You need to route requests to different services based on request characteristics, user preferences, or system requirements

**Cline Prompt Example:**

```
I have multiple AI models (GPT-4, Claude, and local models) and want to route
requests intelligently based on the user's subscription tier and request complexity.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio

class IntelligentLLMRouter:
    def __init__(self):
        # Create model primitives
        self.gpt4_primitive = self._create_model_primitive("gpt-4", self._call_gpt4)
        self.claude_primitive = self._create_model_primitive("claude", self._call_claude)
        self.local_model_primitive = self._create_model_primitive("local", self._call_local_model)

        # Create intelligent router
        self.model_router = RouterPrimitive(
            routes={
                "gpt-4": self.gpt4_primitive,
                "claude": self.claude_primitive,
                "local": self.local_model_primitive
            },
            router_fn=self._route_decision,
            default="local"
        )

    async def process_request(self, prompt: str, user_context: dict) -> dict:
        """Process LLM request with intelligent routing"""
        context = WorkflowContext(
            workflow_id="intelligent-routing",
            metadata={
                "user_tier": user_context.get("tier", "free"),
                "prompt_length": len(prompt),
                "request_type": user_context.get("type", "general")
            }
        )

        try:
            result = await self.model_router.execute(
                {"prompt": prompt, "user_context": user_context},
                context
            )

            # Add routing information to result
            result["routing_info"] = {
                "selected_model": context.state.get("routing_history", ["unknown"])[-1],
                "routing_decision": "tier_and_complexity_based"
            }

            return result

        except Exception as e:
            return {
                "error": "Request processing failed",
                "error_details": str(e),
                "routing_failed": True
            }

    def _route_decision(self, data: dict, context: WorkflowContext) -> str:
        """Intelligent routing logic based on user tier and complexity"""
        user_context = data.get("user_context", {})
        user_tier = user_context.get("tier", "free")
        prompt_length = len(data.get("prompt", ""))

        # Route based on user tier and request complexity
        if user_tier == "premium":
            # Premium users get best models
            if prompt_length > 1000:
                return "gpt-4"  # Complex requests to GPT-4
            else:
                return "claude"  # Standard requests to Claude
        elif user_tier == "pro":
            # Pro users get balanced access
            if prompt_length > 2000:
                return "gpt-4"  # Very complex to GPT-4
            elif prompt_length > 500:
                return "claude"  # Medium complexity to Claude
            else:
                return "local"  # Simple to local model
        else:
            # Free users get local model
            return "local"

    def _create_model_primitive(self, model_name: str, model_func):
        """Create a wrapped model primitive"""

        class ModelPrimitive:
            def __init__(self, model: str, func):
                self.model = model
                self.func = func

            async def execute(self, data: dict, context: WorkflowContext) -> dict:
                try:
                    result = await self.func(data)
                    return {
                        "model_used": self.model,
                        "response": result,
                        "success": True,
                        "model_tier": self._get_model_tier(self.model)
                    }
                except Exception as e:
                    return {
                        "model_used": self.model,
                        "error": str(e),
                        "success": False
                    }

            def _get_model_tier(self, model: str) -> str:
                tier_map = {
                    "gpt-4": "premium",
                    "claude": "pro",
                    "local": "free"
                }
                return tier_map.get(model, "unknown")

        return ModelPrimitive(model_name, model_func)

    async def _call_gpt4(self, data: dict) -> str:
        # Simulate GPT-4 API call
        await asyncio.sleep(2)
        return f"GPT-4 response to: {data['prompt'][:50]}..."

    async def _call_claude(self, data: dict) -> str:
        # Simulate Claude API call
        await asyncio.sleep(1.5)
        return f"Claude response to: {data['prompt'][:50]}..."

    async def _call_local_model(self, data: dict) -> str:
        # Simulate local model call
        await asyncio.sleep(0.5)
        return f"Local model response to: {data['prompt'][:50]}..."

# Usage examples
async def main():
    router = IntelligentLLMRouter()

    # Premium user with complex request
    premium_result = await router.process_request(
        "Write a comprehensive analysis of quantum computing...",
        {"tier": "premium", "type": "analysis"}
    )
    print(f"Premium user routed to: {premium_result['routing_info']['selected_model']}")

    # Free user with simple request
    free_result = await router.process_request(
        "What is 2+2?",
        {"tier": "free", "type": "simple"}
    )
    print(f"Free user routed to: {free_result['routing_info']['selected_model']}")
```

**Cline's Learning Pattern:**

- Identifies multi-provider scenarios that need intelligent routing
- Uses RouterPrimitive with custom routing functions
- Implements tier-based and complexity-based routing logic
- Provides fallback strategies for different user types
- Proper context tracking for routing decisions and analytics

## Example 2: Cost-Optimized Provider Selection

**When to Use:** You need to balance cost and quality by routing to the most appropriate provider based on budget constraints

**Cline Prompt Example:**

```
I want to optimize costs by routing different types of requests to the most
cost-effective LLM provider while maintaining acceptable quality levels.
```

**Expected Implementation:**

```python
from tta_dev-primitives.core.routing import RouterPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio

class CostOptimizedLLMRouter:
    def __init__(self):
        # Provider cost profiles (per 1K tokens)
        self.provider_costs = {
            "gpt-4": 0.03,
            "claude": 0.025,
            "gemini": 0.02,
            "local": 0.001  # Very cheap local model
        }

        # Quality scores (0-1)
        self.provider_quality = {
            "gpt-4": 0.95,
            "claude": 0.92,
            "gemini": 0.88,
            "local": 0.75
        }

        # Create provider primitives
        self.gpt4_primitive = self._create_provider_primitive("gpt-4", self._call_gpt4)
        self.claude_primitive = self._create_provider_primitive("claude", self._call_claude)
        self.gemini_primitive = self._create_provider_primitive("gemini", self._call_gemini)
        self.local_primitive = self._create_provider_primitive("local", self._call_local)

        # Cost-optimized router
        self.cost_router = RouterPrimitive(
            routes={
                "gpt-4": self.gpt4_primitive,
                "claude": self.claude_primitive,
                "gemini": self.gemini_primitive,
                "local": self.local_primitive
            },
            router_fn=self._cost_optimized_routing,
            default="local"
        )

    async def process_request(self, prompt: str, budget_context: dict) -> dict:
        """Process request with cost optimization"""
        context = WorkflowContext(
            workflow_id="cost-optimization",
            metadata={
                "budget_limit": budget_context.get("budget_per_request", 0.01),
                "quality_threshold": budget_context.get("min_quality", 0.7),
                "prompt_tokens": self._estimate_tokens(prompt)
            }
        )

        try:
            result = await self.cost_router.execute(
                {
                    "prompt": prompt,
                    "budget_context": budget_context,
                    "estimated_cost": self._estimate_cost(prompt)
                },
                context
            )

            # Add cost analysis
            result["cost_analysis"] = {
                "selected_provider": context.state.get("routing_history", ["unknown"])[-1],
                "estimated_cost": self._estimate_cost(prompt),
                "cost_vs_budget": self._compare_cost_to_budget(prompt, budget_context),
                "quality_score": self.provider_quality.get(result.get("provider_used", ""), 0)
            }

            return result

        except Exception as e:
            return {
                "error": "Cost-optimized routing failed",
                "error_details": str(e)
            }

    def _cost_optimized_routing(self, data: dict, context: WorkflowContext) -> str:
        """Route based on cost optimization and quality requirements"""
        budget_context = data.get("budget_context", {})
        budget_limit = budget_context.get("budget_per_request", 0.01)
        quality_threshold = budget_context.get("min_quality", 0.7)
        prompt_tokens = self._estimate_tokens(data.get("prompt", ""))

        # Calculate costs for each provider
        provider_options = []
        for provider, cost_per_1k in self.provider_costs.items():
            estimated_cost = (prompt_tokens / 1000) * cost_per_1k
            quality = self.provider_quality[provider]

            # Only consider providers within budget and quality threshold
            if estimated_cost <= budget_limit and quality >= quality_threshold:
                provider_options.append((provider, estimated_cost, quality))

        if not provider_options:
            # No providers meet requirements, use local as fallback
            return "local"

        # Select best cost-quality ratio
        best_provider = min(
            provider_options,
            key=lambda x: x[1] / x[2]  # Cost per quality unit
        )

        return best_provider[0]

    def _estimate_tokens(self, prompt: str) -> int:
        """Rough token estimation (4 chars per token)"""
        return len(prompt) // 4

    def _estimate_cost(self, prompt: str) -> float:
        """Estimate cost for local provider as baseline"""
        tokens = self._estimate_tokens(prompt)
        return (tokens / 1000) * self.provider_costs["local"]

    def _compare_cost_to_budget(self, prompt: str, budget_context: dict) -> str:
        """Compare estimated cost to budget"""
        estimated = self._estimate_cost(prompt)
        budget = budget_context.get("budget_per_request", 0.01)

        if estimated <= budget * 0.5:
            return "well_under_budget"
        elif estimated <= budget:
            return "within_budget"
        else:
            return "over_budget"

    def _create_provider_primitive(self, provider_name: str, provider_func):
        """Create a wrapped provider primitive"""

        class ProviderPrimitive:
            def __init__(self, provider: str, func):
                self.provider = provider
                self.func = func

            async def execute(self, data: dict, context: WorkflowContext) -> dict:
                try:
                    result = await self.func(data)
                    return {
                        "provider_used": self.provider,
                        "response": result,
                        "success": True,
                        "cost_per_1k_tokens": self.provider_costs[self.provider],
                        "quality_score": self.provider_quality[self.provider]
                    }
                except Exception as e:
                    return {
                        "provider_used": self.provider,
                        "error": str(e),
                        "success": False
                    }

        return ProviderPrimitive(provider_name, provider_func)

    async def _call_gpt4(self, data: dict) -> str:
        await asyncio.sleep(2)
        return f"GPT-4 response: {data['prompt'][:50]}..."

    async def _call_claude(self, data: dict) -> str:
        await asyncio.sleep(1.5)
        return f"Claude response: {data['prompt'][:50]}..."

    async def _call_gemini(self, data: dict) -> str:
        await asyncio.sleep(1.2)
        return f"Gemini response: {data['prompt'][:50]}..."

    async def _call_local(self, data: dict) -> str:
        await asyncio.sleep(0.3)
        return f"Local response: {data['prompt'][:50]}..."

# Usage examples
async def main():
    router = CostOptimizedLLMRouter()

    # Tight budget, high quality requirement
    result1 = await router.process_request(
        "Explain quantum computing",
        {"budget_per_request": 0.005, "min_quality": 0.8}
    )
    print(f"Tight budget routed to: {result1['cost_analysis']['selected_provider']}")

    # Loose budget, high quality requirement
    result2 = await router.process_request(
        "Write a comprehensive report on AI ethics",
        {"budget_per_request": 0.05, "min_quality": 0.9}
    )
    print(f"Loose budget routed to: {result2['cost_analysis']['selected_provider']}")

    # Very tight budget
    result3 = await router.process_request(
        "What is 2+2?",
        {"budget_per_request": 0.001, "min_quality": 0.6}
    )
    print(f"Very tight budget routed to: {result3['cost_analysis']['selected_provider']}")
```

**Cline's Learning Pattern:**

- Identifies cost optimization scenarios in multi-provider setups
- Uses RouterPrimitive with cost-quality balancing logic
- Implements budget-aware routing with quality thresholds
- Provides cost analysis and provider comparison
- Proper estimation and fallback strategies

## Example 3: Performance-Based Routing

**When to Use:** You need to route requests to the fastest or most reliable provider based on real-time performance metrics

**Cline Prompt Example:**

```
I want to route requests to the fastest LLM provider based on current response times
and availability, with automatic failover to backup providers.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio
import time
from collections import deque

class PerformanceBasedLLMRouter:
    def __init__(self):
        # Performance tracking
        self.performance_history = {
            "gpt-4": deque(maxlen=100),
            "claude": deque(maxlen=100),
            "gemini": deque(maxlen=100),
            "local": deque(maxlen=100)
        }
        self.availability_status = {
            "gpt-4": True,
            "claude": True,
            "gemini": True,
            "local": True
        }

        # Create provider primitives
        self.gpt4_primitive = self._create_performance_primitive("gpt-4", self._call_gpt4)
        self.claude_primitive = self._create_performance_primitive("claude", self._call_claude)
        self.gemini_primitive = self._create_performance_primitive("gemini", self._call_gemini)
        self.local_primitive = self._create_performance_primitive("local", self._call_local)

        # Performance-based router
        self.performance_router = RouterPrimitive(
            routes={
                "gpt-4": self.gpt4_primitive,
                "claude": self.claude_primitive,
                "gemini": self.gemini_primitive,
                "local": self.local_primitive
            },
            router_fn=self._performance_based_routing,
            default="local"
        )

    async def process_request(self, prompt: str, performance_context: dict) -> dict:
        """Process request with performance-based routing"""
        context = WorkflowContext(
            workflow_id="performance-routing",
            metadata={
                "request_priority": performance_context.get("priority", "normal"),
                "timeout_requirement": performance_context.get("max_wait_time", 5.0)
            }
        )

        try:
            result = await self.performance_router.execute(
                {"prompt": prompt, "performance_context": performance_context},
                context
            )

            # Add performance metrics
            selected_provider = context.state.get("routing_history", ["unknown"])[-1]
            avg_performance = self._get_average_performance(selected_provider)

            result["performance_metrics"] = {
                "selected_provider": selected_provider,
                "average_response_time": avg_performance,
                "routing_strategy": "performance_based",
                "provider_available": self.availability_status.get(selected_provider, False)
            }

            return result

        except Exception as e:
            return {
                "error": "Performance routing failed",
                "error_details": str(e),
                "fallback_used": True
            }

    def _performance_based_routing(self, data: dict, context: WorkflowContext) -> str:
        """Route based on current performance metrics"""
        performance_context = data.get("performance_context", {})
        priority = performance_context.get("priority", "normal")
        max_wait = performance_context.get("max_wait_time", 5.0)

        # Get available providers
        available_providers = [
            provider for provider, available in self.availability_status.items()
            if available
        ]

        if not available_providers:
            return "local"  # Fallback

        # Calculate performance scores
        provider_scores = []
        for provider in available_providers:
            avg_time = self._get_average_performance(provider)

            # Skip providers that are too slow for high-priority requests
            if priority == "high" and avg_time > max_wait:
                continue

            # Calculate performance score (lower time = higher score)
            performance_score = 1.0 / (avg_time + 0.1)  # Add small constant to avoid division by zero

            provider_scores.append((provider, performance_score, avg_time))

        if not provider_scores:
            # No providers meet requirements, use fastest available
            fastest_provider = min(
                [(p, self._get_average_performance(p)) for p in available_providers],
                key=lambda x: x[1]
            )
            return fastest_provider[0]

        # Select best performing provider
        best_provider = max(provider_scores, key=lambda x: x[1])
        return best_provider[0]

    def _get_average_performance(self, provider: str) -> float:
        """Get average response time for provider"""
        history = self.performance_history.get(provider, deque())
        if not history:
            return 2.0  # Default 2 seconds if no history

        return sum(history) / len(history)

    def _update_performance(self, provider: str, response_time: float):
        """Update performance metrics"""
        self.performance_history[provider].append(response_time)

        # Mark as unavailable if consistently slow (> 10 seconds for 5 consecutive requests)
        slow_requests = list(self.performance_history[provider])[-5:]
        if len(slow_requests) >= 5 and all(t > 10 for t in slow_requests):
            self.availability_status[provider] = False

    def _create_performance_primitive(self, provider_name: str, provider_func):
        """Create a performance-tracking provider primitive"""

        class PerformancePrimitive:
            def __init__(self, provider: str, func, router_instance):
                self.provider = provider
                self.func = func
                self.router = router_instance

            async def execute(self, data: dict, context: WorkflowContext) -> dict:
                start_time = time.time()

                try:
                    result = await self.func(data)
                    response_time = time.time() - start_time

                    # Update performance metrics
                    self.router._update_performance(self.provider, response_time)

                    return {
                        "provider_used": self.provider,
                        "response": result,
                        "success": True,
                        "response_time": response_time
                    }
                except Exception as e:
                    response_time = time.time() - start_time

                    # Update performance even for failures
                    self.router._update_performance(self.provider, response_time)

                    return {
                        "provider_used": self.provider,
                        "error": str(e),
                        "success": False,
                        "response_time": response_time
                    }

        return PerformancePrimitive(provider_name, provider_func, self)

    async def _call_gpt4(self, data: dict) -> str:
        await asyncio.sleep(2.5)
        return f"GPT-4 response: {data['prompt'][:50]}..."

    async def _call_claude(self, data: dict) -> str:
        await asyncio.sleep(1.8)
        return f"Claude response: {data['prompt'][:50]}..."

    async def _call_gemini(self, data: dict) -> str:
        await asyncio.sleep(1.2)
        return f"Gemini response: {data['prompt'][:50]}..."

    async def _call_local(self, data: dict) -> str:
        await asyncio.sleep(0.3)
        return f"Local response: {data['prompt'][:50]}..."

# Usage examples
async def main():
    router = PerformanceBasedLLMRouter()

    # High priority request
    result1 = await router.process_request(
        "Urgent: Analyze this security threat",
        {"priority": "high", "max_wait_time": 2.0}
    )
    print(f"High priority routed to: {result1['performance_metrics']['selected_provider']}")

    # Normal priority request
    result2 = await router.process_request(
        "Write a blog post about AI trends",
        {"priority": "normal", "max_wait_time": 5.0}
    )
    print(f"Normal priority routed to: {result2['performance_metrics']['selected_provider']}")

    # Low priority request
    result3 = await router.process_request(
        "What is the weather like?",
        {"priority": "low", "max_wait_time": 10.0}
    )
    print(f"Low priority routed to: {result3['performance_metrics']['selected_provider']}")
```

**Cline's Learning Pattern:**

- Identifies performance optimization needs in multi-provider scenarios
- Uses RouterPrimitive with real-time performance tracking
- Implements availability monitoring and automatic failover
- Provides response time metrics and provider performance analytics
- Priority-based routing with timeout awareness

## Example 4: Geographic Routing

**When to Use:** You need to route requests to the geographically closest or most appropriate regional endpoint

**Cline Prompt Example:**

```
I have LLM services deployed in multiple regions (US, Europe, Asia) and want to
route requests to the closest region to reduce latency and comply with data regulations.
```

**Expected Implementation:**

```python
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.core.base import WorkflowContext
import asyncio
import time

class GeographicLLMRouter:
    def __init__(self):
        # Regional endpoints and their characteristics
        self.regional_endpoints = {
            "us-east": {
                "endpoint": "https://api.us-east.example.com",
                "latency_profile": {"us": 50, "europe": 150, "asia": 250},
                "data_compliance": ["US", "Canada"],
                "availability": 0.99
            },
            "eu-west": {
                "endpoint": "https://api.eu-west.example.com",
                "latency_profile": {"us": 120, "europe": 40, "asia": 280},
                "data_compliance": ["EU", "UK"],
                "availability": 0.98
            },
            "asia-pacific": {
                "endpoint": "https://api.asia-pacific.example.com",
                "latency_profile": {"us": 200, "europe": 250, "asia": 60},
                "data_compliance": ["Japan", "Singapore", "Australia"],
                "availability": 0.97
            }
        }

        # Create regional primitives
        self.us_east_primitive = self._create_regional_primitive("us-east", self._call_us_east)
        self.eu_west_primitive = self._create_regional_primitive("eu-west", self._call_eu_west)
        self.asia_pacific_primitive = self._create_regional_primitive("asia-pacific", self._call_asia_pacific)

        # Geographic router
        self.geo_router = RouterPrimitive(
            routes={
                "us-east": self.us_east_primitive,
                "eu-west": self.eu_west_primitive,
                "asia-pacific": self.asia_pacific_primitive
            },
            router_fn=self._geographic_routing,
            default="us-east"
        )

    async def process_request(self, prompt: str, geo_context: dict) -> dict:
        """Process request with geographic optimization"""
        context = WorkflowContext(
            workflow_id="geographic-routing",
            metadata={
                "user_region": geo_context.get("user_region", "us"),
                "data_classification": geo_context.get("data_classification", "public"),
                "compliance_requirements": geo_context.get("compliance_requirements", [])
            }
        )

        try:
            result = await self.geo_router.execute(
                {"prompt": prompt, "geo_context": geo_context},
                context
            )

            # Add geographic routing information
            selected_region = context.state.get("routing_history", ["unknown"])[-1]
            endpoint_info = self.regional_endpoints.get(selected_region, {})

            result["geographic_info"] = {
                "selected_region": selected_region,
                "endpoint": endpoint_info.get("endpoint"),
                "routing_reason": self._get_routing_reason(geo_context, selected_region),
                "estimated_latency": endpoint_info.get("latency_profile", {}).get(
                    geo_context.get("user_region", "us"), 999
                )
            }

            return result

        except Exception as e:
            return {
                "error": "Geographic routing failed",
                "error_details": str(e),
                "routing_failed": True
            }

    def _geographic_routing(self, data: dict, context: WorkflowContext) -> str:
        """Route based on geographic location and compliance requirements"""
        geo_context = data.get("geo_context", {})
        user_region = geo_context.get("user_region", "us")
        data_classification = geo_context.get("data_classification", "public")
        compliance_reqs = geo_context.get("compliance_requirements", [])

        # Find compliant regions
        compliant_regions = []
        for region, info in self.regional_endpoints.items():
            # Check data compliance
            if data_classification == "public" or info.get("availability", 0) > 0.9:
                compliant_regions.append(region)

        if not compliant_regions:
            return "us-east"  # Default fallback

        # Calculate latency scores for each compliant region
        region_scores = []
        for region in compliant_regions:
            endpoint_info = self.regional_endpoints[region]
            latency = endpoint_info.get("latency_profile", {}).get(user_region, 300)

            # Lower latency is better
            latency_score = 1.0 / (latency + 10)  # Add constant to avoid division by zero

            region_scores.append((region, latency_score, latency))

        # Select best region
        if region_scores:
            best_region = max(region_scores, key=lambda x: x[1])
            return best_region[0]

        return "us-east"  # Final fallback

    def _get_routing_reason(self, geo_context: dict, selected_region: str) -> str:
        """Explain why this region was selected"""
        user_region = geo_context.get("user_region", "us")
        data_classification = geo_context.get("data_classification", "public")

        if data_classification == "restricted":
            return f"compliance_with_{selected_region}_regulations"
        elif user_region == "eu" and selected_region == "eu-west":
            return "lowest_latency_for_eu_users"
        elif user_region == "asia" and selected_region == "asia-pacific":
            return "lowest_latency_for_asia_users"
        else:
            return "default_regional_routing"

    def _create_regional_primitive(self, region_name: str, region_func):
        """Create a regional provider primitive"""

        class RegionalPrimitive:
            def __init__(self, region: str, func):
                self.region = region
                self.func = func

            async def execute(self, data: dict, context: WorkflowContext) -> dict:
                start_time = time.time()

                try:
                    result = await self.func(data)
                    response_time = time.time() - start_time

                    return {
                        "region_used": self.region,
                        "response": result,
                        "success": True,
                        "response_time": response_time,
                        "endpoint": self._get_endpoint(self.region)
                    }
                except Exception as e:
                    return {
                        "region_used": self.region,
                        "error": str(e),
                        "success": False
                    }

            def _get_endpoint(self, region: str) -> str:
                return self.regional_endpoints.get(region, {}).get("endpoint", "unknown")

        return RegionalPrimitive(region_name, region_func)

    async def _call_us_east(self, data: dict) -> str:
        await asyncio.sleep(1.5)
        return f"US-East response: {data['prompt'][:50]}..."

    async def _call_eu_west(self, data: dict) -> str:
        await asyncio.sleep(1.3)
        return f"EU-West response: {data['prompt'][:50]}..."

    async def _call_asia_pacific(self, data: dict) -> str:
        await asyncio.sleep(1.1)
        return f"Asia-Pacific response: {data['prompt'][:50]}..."

# Usage examples
async def main():
    router = GeographicLLMRouter()

    # EU user with compliance requirements
    result1 = await router.process_request(
        "Process customer data",
        {
            "user_region": "eu",
            "data_classification": "restricted",
            "compliance_requirements": ["GDPR"]
        }
    )
    print(f"EU user routed to: {result1['geographic_info']['selected_region']}")

    # US user with normal data
    result2 = await router.process_request(
        "Generate marketing content",
        {
            "user_region": "us",
            "data_classification": "public"
        }
    )
    print(f"US user routed to: {result2['geographic_info']['selected_region']}")

    # Asia user
    result3 = await router.process_request(
        "Analyze market trends",
        {
            "user_region": "asia",
            "data_classification": "public"
        }
    )
    print(f"Asia user routed to: {result3['geographic_info']['selected_region']}")
```

**Cline's Learning Pattern:**

- Identifies multi-region deployment scenarios
- Uses RouterPrimitive with geographic optimization logic
- Implements compliance-aware routing for data regulations
- Provides latency estimation and regional performance metrics
- Smart fallback strategies for different user regions

## Cline Detection Patterns

**RouterPrimitive Indicators:**

- "route requests to different providers"
- "intelligent routing based on"
- "optimize cost and performance"
- "load balancing across services"
- "geographic routing"
- "provider selection based on"
- "route to the best option"
- "cost-optimized routing"
- "performance-based routing"

**Cline's Response Strategy:**

1. Identify multi-provider scenarios that need intelligent routing
2. Use RouterPrimitive with custom routing functions
3. Implement routing logic based on cost, performance, geography, or requirements
4. Add proper fallback strategies and error handling
5. Use WorkflowContext for routing decision tracking and analytics

## Common Mistakes to Avoid

❌ **Wrong:** Hard-coded routing without optimization

```python
# Always use the same provider
def route_request(data):
    return "gpt-4"  # Not intelligent
```

✅ **Right:** Intelligent routing based on context

```python
# Smart routing based on requirements
def route_request(data, context):
    if context.metadata.get("budget") < 0.01:
        return "local"
    return "gpt-4"
```

❌ **Wrong:** No default route

```python
# Can fail if router_fn returns unknown route
router = RouterPrimitive(routes=routes, router_fn=route_fn)  # No default!
```

✅ **Right:** Always provide a default route

```python
# Safe routing with fallback
router = RouterPrimitive(
    routes=routes,
    router_fn=route_fn,
    default="local"  # Safe fallback
)
```

❌ **Wrong:** No routing decision logging

```python
# Can't track routing patterns
router = RouterPrimitive(routes=routes, router_fn=route_fn, default="local")
```

✅ **Right:** Track routing decisions

```python
# Enable routing analytics
context = WorkflowContext(workflow_id="routing-service")
result = await router.execute(data, context)
# Routing history is automatically tracked in context.state["routing_history"]
```

---

**Next Steps:** When cline detects routing scenarios in multi-provider systems, it should automatically suggest RouterPrimitive with intelligent routing strategies based on cost, performance, geography, or user requirements.
