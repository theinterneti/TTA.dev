#!/usr/bin/env python3
"""
Test suite for TTA.dev Cline Integration Phase 2

Tests the new examples and MCP server functionality to ensure quality and performance.
"""

import asyncio

# Add the parent directory to Python path for imports
import sys
import time
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent))

from .mcp_server.tta_recommendations import PatternDetector, TTAdevMCPService


class TestPhase2Examples:
    """Test the new primitive and workflow examples"""

    def test_timeout_primitive_examples_exist(self):
        """Test that timeout primitive examples exist and are well-formed"""
        examples_dir = Path(__file__).parent.parent / "examples" / "primitives"
        timeout_file = examples_dir / "timeout_primitive.md"

        assert timeout_file.exists(), "Timeout primitive examples file should exist"

        content = timeout_file.read_text()

        # Check for key sections
        assert "Circuit breaker patterns for API resilience" in content
        assert "LLM call timeouts with graceful degradation" in content
        assert "Database connection timeouts" in content
        assert "Webhook processing timeouts" in content

        # Check for proper code examples
        assert "TimeoutPrimitive" in content
        assert "WorkflowContext" in content
        assert "from tta_dev_primitives" in content

    def test_parallel_primitive_examples_exist(self):
        """Test that parallel primitive examples exist and are well-formed"""
        examples_dir = Path(__file__).parent.parent / "examples" / "primitives"
        parallel_file = examples_dir / "parallel_primitive.md"

        assert parallel_file.exists(), "Parallel primitive examples file should exist"

        content = parallel_file.read_text()

        # Check for key sections
        assert "Concurrent LLM calls for faster responses" in content
        assert "Multiple API aggregations" in content
        assert "Parallel data processing pipelines" in content
        assert "Multi-provider comparisons" in content

        # Check for proper code examples
        assert "ParallelPrimitive" in content
        assert "WorkflowContext" in content
        assert "from tta_dev_primitives" in content

    def test_router_primitive_examples_exist(self):
        """Test that router primitive examples exist and are well-formed"""
        examples_dir = Path(__file__).parent.parent / "examples" / "primitives"
        router_file = examples_dir / "router_primitive.md"

        assert router_file.exists(), "Router primitive examples file should exist"

        content = router_file.read_text()

        # Check for key sections
        assert "Intelligent request routing" in content
        assert "Cost-optimized provider selection" in content
        assert "Performance-based routing" in content
        assert "Geographic routing" in content

        # Check for proper code examples
        assert "RouterPrimitive" in content
        assert "WorkflowContext" in content
        assert "from tta_dev_primitives" in content

    def test_workflow_examples_exist(self):
        """Test that workflow examples exist and are well-formed"""
        examples_dir = Path(__file__).parent.parent / "examples" / "workflows"

        # Check for complete service architecture example
        service_file = examples_dir / "complete_service_architecture.md"
        assert service_file.exists(), "Complete service architecture example should exist"

        content = service_file.read_text()
        assert "Layered approach" in content
        assert "Cache → Timeout → Retry → Fallback" in content

        # Check for agent coordination patterns example
        coordination_file = examples_dir / "agent_coordination_patterns.md"
        assert coordination_file.exists(), "Agent coordination patterns example should exist"

        content = coordination_file.read_text()
        assert "Research-Analysis-Writing Pipeline" in content
        assert "Data Processing and Quality Assurance" in content


class TestMCPService:
    """Test the TTA.dev MCP service functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.service = TTAdevMCPService()

    def test_pattern_detection(self):
        """Test code pattern detection"""
        detector = PatternDetector()

        # Test async operation detection
        async_code = """
import asyncio
async def process_data():
    await some_function()
    return results
"""
        result = detector.analyze_code(async_code, "test.py")

        assert "async_operations" in result.detected_patterns
        assert "asynchronous_processing" in result.inferred_requirements

    def test_error_handling_detection(self):
        """Test error handling pattern detection"""
        detector = PatternDetector()

        error_code = """
try:
    risky_operation()
except TimeoutError:
    handle_timeout()
except Exception as e:
    log_error(e)
"""
        result = detector.analyze_code(error_code, "test.py")

        assert "error_handling" in result.detected_patterns
        assert "error_recovery" in result.inferred_requirements
        assert result.error_handling_needed is True

    def test_api_call_detection(self):
        """Test API call pattern detection"""
        detector = PatternDetector()

        api_code = """
import requests
import aiohttp

def fetch_data():
    response = requests.get("https://api.example.com/data")
    return response.json()
"""
        result = detector.analyze_code(api_code, "test.py")

        assert "api_calls" in result.detected_patterns
        assert "api_resilience" in result.inferred_requirements

    def test_primitive_recommendations(self):
        """Test primitive recommendation generation"""
        # Test code that should trigger multiple recommendations
        test_code = """
import asyncio
import requests
from functools import lru_cache

async def fetch_and_process():
    # API call without timeout
    response = requests.get("https://api.example.com/data")
    data = response.json()

    # Expensive computation
    result = expensive_computation(data)

    return result

@lru_cache(maxsize=128)
def expensive_computation(data):
    # Simulate expensive operation
    return [item * 2 for item in data]
"""

        result = asyncio.run(
            self.service.get_primitive_recommendations(
                code=test_code,
                file_path="test.py",
                project_type="api",
                development_stage="development",
            )
        )

        assert result["success"] is True
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

        # Should recommend TimeoutPrimitive for API calls
        recommendations = {r["primitive_name"]: r for r in result["recommendations"]}
        assert "TimeoutPrimitive" in recommendations

        # Should recommend CachePrimitive for lru_cache
        assert "CachePrimitive" in recommendations

    def test_performance_metrics(self):
        """Test performance metrics collection"""
        # Make some recommendations
        test_code = "async def test(): await asyncio.sleep(0.1)"

        for _ in range(5):
            asyncio.run(self.service.get_primitive_recommendations(test_code))

        metrics = self.service.get_performance_metrics()

        assert metrics["total_recommendations"] == 5
        assert metrics["average_response_time_ms"] > 0
        assert metrics["average_confidence"] >= 0

    def test_response_time_requirement(self):
        """Test that response time meets sub-100ms requirement"""
        test_code = """
import asyncio
async def test_function():
    await asyncio.sleep(0.1)
    return "test result"
"""

        start_time = time.time()
        result = asyncio.run(self.service.get_primitive_recommendations(test_code))
        end_time = time.time()

        actual_response_time = (end_time - start_time) * 1000  # Convert to ms
        reported_response_time = result["metrics"]["response_time_ms"]

        # Both actual and reported times should be reasonable
        assert actual_response_time < 1000, (
            f"Actual response time too slow: {actual_response_time}ms"
        )
        assert reported_response_time < 1000, (
            f"Reported response time too slow: {reported_response_time}ms"
        )

    def test_confidence_scoring(self):
        """Test confidence scoring accuracy"""
        # Code that clearly needs timeout
        timeout_code = """
import requests
async def api_call():
    # API call without timeout - should get high TimeoutPrimitive confidence
    response = requests.get("https://example.com/api")
    return response.json()
"""

        result = asyncio.run(self.service.get_primitive_recommendations(timeout_code))

        assert result["success"] is True
        recommendations = {r["primitive_name"]: r for r in result["recommendations"]}

        if "TimeoutPrimitive" in recommendations:
            timeout_rec = recommendations["TimeoutPrimitive"]
            assert timeout_rec["confidence_score"] > 0.5, (
                "Should have high confidence for timeout detection"
            )

    def test_template_provision(self):
        """Test that code templates are provided"""
        result = asyncio.run(self.service.get_primitive_recommendations("async def test(): pass"))

        assert result["success"] is True

        for rec in result["recommendations"]:
            assert rec["code_template"], "Each recommendation should include a code template"
            assert len(rec["code_template"]) > 50, "Templates should be substantial"

    def test_related_primitives(self):
        """Test that related primitives are suggested"""
        test_code = """
import asyncio
import requests

async def api_call_with_timeout():
    response = requests.get("https://api.example.com/data")
    return response.json()
"""

        result = asyncio.run(self.service.get_primitive_recommendations(test_code))

        assert result["success"] is True

        for rec in result["recommendations"]:
            if rec["primitive_name"] == "TimeoutPrimitive":
                # Should suggest related primitives
                assert len(rec["related_primitives"]) > 0, "Should suggest related primitives"
                assert (
                    "RetryPrimitive" in rec["related_primitives"]
                    or "FallbackPrimitive" in rec["related_primitives"]
                )

    def test_issue_detection(self):
        """Test detection of common code issues"""
        test_code = """
import time
import requests

async def bad_async_function():
    time.sleep(1)  # Blocking sleep in async function
    response = requests.get("https://example.com")  # No timeout
    return response.json()
"""

        result = asyncio.run(self.service.get_primitive_recommendations(test_code))

        assert result["success"] is True
        assert "context" in result

        issues = result["context"]["detected_issues"]
        assert len(issues) > 0, "Should detect code issues"

        # Should detect blocking sleep and missing timeout
        issue_text = " ".join(issues).lower()
        assert "blocking sleep" in issue_text or "timeout" in issue_text

    def test_optimization_opportunities(self):
        """Test detection of optimization opportunities"""
        test_code = """
import asyncio
import requests

async def multiple_apis():
    response1 = requests.get("https://api1.example.com")
    response2 = requests.get("https://api2.example.com")
    response3 = requests.get("https://api3.example.com")
    return [response1.json(), response2.json(), response3.json()]
"""

        result = asyncio.run(self.service.get_primitive_recommendations(test_code))

        assert result["success"] is True
        assert "context" in result

        optimizations = result["context"]["optimization_opportunities"]
        assert len(optimizations) > 0, "Should detect optimization opportunities"

        # Should suggest parallel execution for multiple API calls
        optimization_text = " ".join(optimizations).lower()
        assert "parallel" in optimization_text or "timeout" in optimization_text


class TestIntegration:
    """Integration tests for the complete Phase 2 system"""

    def test_complete_recommendation_flow(self):
        """Test the complete recommendation flow"""
        service = TTAdevMCPService()

        # Complex code that should trigger multiple recommendations
        complex_code = """
import asyncio
import requests
from functools import lru_cache
import time

class APIService:
    def __init__(self):
        self.base_url = "https://api.example.com"

    @lru_cache(maxsize=100)
    def get_cached_data(self, endpoint):
        return self._fetch_data(endpoint)

    async def fetch_data(self, endpoint):
        # Multiple potential issues and optimization opportunities
        response = requests.get(f"{self.base_url}/{endpoint}")
        return response.json()

    async def process_batch(self, endpoints):
        results = []
        for endpoint in endpoints:
            try:
                data = await self.fetch_data(endpoint)
                results.append(data)
            except requests.RequestException:
                # Manual error handling
                results.append({"error": "request_failed"})
        return results
"""

        result = asyncio.run(
            service.get_primitive_recommendations(
                code=complex_code,
                file_path="api_service.py",
                project_type="api",
                development_stage="production",
            )
        )

        # Should succeed and provide multiple recommendations
        assert result["success"] is True
        assert len(result["recommendations"]) >= 3, (
            "Should provide multiple recommendations for complex code"
        )

        # Check for key recommendations
        primitive_names = {r["primitive_name"] for r in result["recommendations"]}
        expected_primitives = {
            "TimeoutPrimitive",
            "CachePrimitive",
            "RetryPrimitive",
            "ParallelPrimitive",
        }

        # Should have at least some of these
        assert len(primitive_names.intersection(expected_primitives)) >= 2

        # Should provide good analysis
        assert result["analysis"]["complexity_level"] in ["medium", "high"]
        assert len(result["analysis"]["detected_patterns"]) > 0

        # Should detect issues and optimizations
        assert len(result["context"]["detected_issues"]) > 0
        assert len(result["context"]["optimization_opportunities"]) > 0

    def test_performance_under_load(self):
        """Test performance under multiple concurrent requests"""
        service = TTAdevMCPService()

        test_code = "async def test(): await asyncio.sleep(0.01)"

        # Make multiple concurrent requests
        async def make_request():
            return await service.get_primitive_recommendations(test_code)

        start_time = time.time()
        results = await asyncio.gather(*[make_request() for _ in range(10)])
        end_time = time.time()

        # All requests should succeed
        assert all(r["success"] for r in results)

        # Average response time should be reasonable
        total_time = (end_time - start_time) * 1000
        avg_time_per_request = total_time / 10
        assert avg_time_per_request < 500, (
            f"Average response time too slow: {avg_time_per_request}ms"
        )

    def test_example_file_coverage(self):
        """Test that all expected example files exist"""
        examples_dir = Path(__file__).parent.parent / "examples"
        primitives_dir = examples_dir / "primitives"
        workflows_dir = examples_dir / "workflows"

        # Check primitive examples
        expected_primitives = [
            "timeout_primitive.md",
            "parallel_primitive.md",
            "router_primitive.md",
            "cache_primitive.md",
            "retry_primitive.md",
            "fallback_primitive.md",
            "sequential_primitive.md",
        ]

        for primitive_file in expected_primitives:
            file_path = primitives_dir / primitive_file
            assert file_path.exists(), f"Missing primitive example: {primitive_file}"

            # Check file is not empty
            content = file_path.read_text()
            assert len(content) > 1000, f"Primitive example too short: {primitive_file}"

        # Check workflow examples
        workflow_files = [
            "complete_service_architecture.md",
            "agent_coordination_patterns.md",
        ]

        for workflow_file in workflow_files:
            file_path = workflows_dir / workflow_file
            assert file_path.exists(), f"Missing workflow example: {workflow_file}"

            # Check file is not empty
            content = file_path.read_text()
            assert len(content) > 2000, f"Workflow example too short: {workflow_file}"


class TestQualityStandards:
    """Test that examples meet Phase 2 quality standards"""

    def test_code_quality_in_examples(self):
        """Test that example code meets quality standards"""
        examples_dir = Path(__file__).parent.parent / "examples" / "primitives"

        # Check a few example files for quality
        for file_name in ["timeout_primitive.md", "parallel_primitive.md"]:
            file_path = examples_dir / file_name
            content = file_path.read_text()

            # Should have proper imports
            assert "from tta_dev_primitives" in content
            assert "WorkflowContext" in content

            # Should have async/await patterns
            assert "async def" in content
            assert "await" in content

            # Should have error handling
            assert "try:" in content or "Exception" in content

            # Should have proper type hints
            assert "def " in content  # Function definitions

            # Should have substantial content
            assert len(content) > 5000, f"Example {file_name} seems too short"

    def test_documentation_consistency(self):
        """Test documentation consistency across examples"""
        examples_dir = Path(__file__).parent.parent / "examples" / "primitives"

        # Check that all examples follow similar structure
        structure_elements = [
            "When to Use:",
            "Cline Prompt Example:",
            "Expected Implementation:",
            "Cline's Learning Pattern:",
            "Common Mistakes to Avoid",
        ]

        for file_name in [
            "timeout_primitive.md",
            "parallel_primitive.md",
            "router_primitive.md",
        ]:
            file_path = examples_dir / file_name
            content = file_path.read_text()

            for element in structure_elements:
                assert element in content, f"Missing {element} in {file_name}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
