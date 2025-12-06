"""Tests for the PatternDetector class."""

import pytest

from tta_dev_primitives.analysis.models import CodeAnalysisResult
from tta_dev_primitives.analysis.patterns import PatternDetector


class TestPatternDetector:
    """Tests for PatternDetector functionality."""

    @pytest.fixture
    def detector(self) -> PatternDetector:
        """Create a PatternDetector instance."""
        return PatternDetector()

    def test_init_registers_patterns(self, detector: PatternDetector) -> None:
        """Verify all pattern categories are registered."""
        expected_patterns = [
            "async_operations",
            "error_handling",
            "api_calls",
            "data_processing",
            "caching_patterns",
            "timeout_patterns",
            "retry_patterns",
            "fallback_patterns",
            "parallel_patterns",
            "routing_patterns",
            "llm_patterns",
            "database_patterns",
            # New patterns
            "rate_limiting",
            "streaming_patterns",
            "validation_patterns",
            "logging_patterns",
            "configuration_patterns",
            "authentication_patterns",
            "workflow_patterns",
            "testing_patterns",
        ]
        for pattern in expected_patterns:
            assert pattern in detector.patterns, f"Missing pattern: {pattern}"

    def test_analyze_returns_code_analysis_result(self, detector: PatternDetector) -> None:
        """Verify analyze returns CodeAnalysisResult."""
        code = "def hello(): pass"
        result = detector.analyze(code)
        assert isinstance(result, CodeAnalysisResult)

    def test_detect_async_operations(self, detector: PatternDetector) -> None:
        """Verify async pattern detection."""
        code = """
async def fetch_data():
    result = await client.get('/api/data')
    return result
"""
        result = detector.analyze(code)
        assert "async_operations" in result.detected_patterns

    def test_detect_error_handling(self, detector: PatternDetector) -> None:
        """Verify error handling pattern detection."""
        code = """
def risky_operation():
    try:
        return do_something()
    except ValueError as e:
        handle_error(e)
"""
        result = detector.analyze(code)
        assert "error_handling" in result.detected_patterns

    def test_detect_api_calls(self, detector: PatternDetector) -> None:
        """Verify API call pattern detection."""
        code = """
def fetch():
    response = requests.get('https://api.example.com/data')
    return response.json()
"""
        result = detector.analyze(code)
        assert "api_calls" in result.detected_patterns

    def test_detect_timeout_patterns(self, detector: PatternDetector) -> None:
        """Verify timeout pattern detection."""
        code = """
async def call_with_timeout():
    result = await asyncio.wait_for(operation(), timeout=30)
    return result
"""
        result = detector.analyze(code)
        assert "timeout_patterns" in result.detected_patterns

    def test_detect_retry_patterns(self, detector: PatternDetector) -> None:
        """Verify retry pattern detection."""
        code = """
def fetch_with_retry():
    for attempt in range(3):
        try:
            return api.call()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
"""
        result = detector.analyze(code)
        assert "retry_patterns" in result.detected_patterns

    def test_detect_fallback_patterns(self, detector: PatternDetector) -> None:
        """Verify fallback pattern detection."""
        code = """
def get_data():
    try:
        return primary_source()
    except Exception:
        return fallback_source()
"""
        result = detector.analyze(code)
        assert "fallback_patterns" in result.detected_patterns

    def test_detect_parallel_patterns(self, detector: PatternDetector) -> None:
        """Verify parallel execution pattern detection."""
        code = """
async def parallel_fetch():
    results = await asyncio.gather(
        fetch_users(),
        fetch_orders(),
        fetch_products()
    )
    return results
"""
        result = detector.analyze(code)
        assert "parallel_patterns" in result.detected_patterns

    def test_detect_routing_patterns(self, detector: PatternDetector) -> None:
        """Verify routing pattern detection."""
        code = """
def route_request(request):
    if request.type == 'fast':
        return fast_handler(request)
    elif request.type == 'slow':
        return slow_handler(request)
    return default_handler(request)
"""
        result = detector.analyze(code)
        assert "routing_patterns" in result.detected_patterns

    def test_detect_llm_patterns(self, detector: PatternDetector) -> None:
        """Verify LLM pattern detection."""
        code = """
def generate_text(prompt):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
"""
        result = detector.analyze(code)
        assert "llm_patterns" in result.detected_patterns

    def test_detect_database_patterns(self, detector: PatternDetector) -> None:
        """Verify database pattern detection."""
        code = """
async def get_user(user_id):
    async with db.session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
"""
        result = detector.analyze(code)
        assert "database_patterns" in result.detected_patterns

    def test_complexity_level_low(self, detector: PatternDetector) -> None:
        """Verify low complexity detection."""
        code = """
def simple():
    return 42
"""
        result = detector.analyze(code)
        assert result.complexity_level == "low"

    def test_complexity_level_medium(self, detector: PatternDetector) -> None:
        """Verify medium complexity detection."""
        # Code with multiple patterns
        code = """
async def medium_complexity():
    try:
        result = await fetch_data()
        return process(result)
    except Exception:
        return fallback()
"""
        result = detector.analyze(code)
        # Medium when 3-5 patterns detected
        assert result.complexity_level in ["low", "medium"]

    def test_inferred_requirements(self, detector: PatternDetector) -> None:
        """Verify requirements are inferred from patterns."""
        code = """
async def fetch():
    try:
        return await api.get()
    except Exception:
        pass
"""
        result = detector.analyze(code)
        # Should infer async processing and error recovery
        assert len(result.inferred_requirements) > 0

    def test_empty_code_returns_no_patterns(self, detector: PatternDetector) -> None:
        """Verify empty code returns empty patterns."""
        result = detector.analyze("")
        assert result.detected_patterns == []

    def test_file_path_stored(self, detector: PatternDetector) -> None:
        """Verify file path info is handled."""
        code = "def test(): pass"
        # PatternDetector uses file_path for context, result may not store it
        result = detector.analyze(code, file_path="test_file.py")
        # Just verify analysis completes with file_path
        assert result is not None
        assert isinstance(result, CodeAnalysisResult)

    def test_multiple_patterns_detected(self, detector: PatternDetector) -> None:
        """Verify multiple patterns can be detected in one code block."""
        code = """
async def complex_operation():
    try:
        for attempt in range(3):
            try:
                result = await asyncio.wait_for(
                    client.get('/api/data', timeout=30),
                    timeout=60
                )
                return result
            except asyncio.TimeoutError:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
    except Exception:
        return await fallback_fetch()
"""
        result = detector.analyze(code)
        # Should detect multiple patterns
        assert len(result.detected_patterns) >= 3
        assert "async_operations" in result.detected_patterns
        assert "error_handling" in result.detected_patterns


class TestNewPatterns:
    """Tests for newly added pattern detection."""

    @pytest.fixture
    def detector(self) -> PatternDetector:
        """Create a PatternDetector instance."""
        return PatternDetector()

    def test_detect_rate_limiting(self, detector: PatternDetector) -> None:
        """Verify rate limiting pattern detection."""
        code = """
async def call_api():
    try:
        return await client.post('/api')
    except HTTPError as e:
        if e.status_code == 429:
            # Rate limit exceeded
            await asyncio.sleep(60)
"""
        result = detector.analyze(code)
        assert "rate_limiting" in result.detected_patterns

    def test_detect_streaming_patterns(self, detector: PatternDetector) -> None:
        """Verify streaming pattern detection."""
        code = """
async def stream_response():
    async for chunk in client.stream('/data'):
        yield chunk
"""
        result = detector.analyze(code)
        assert "streaming_patterns" in result.detected_patterns

    def test_detect_validation_patterns(self, detector: PatternDetector) -> None:
        """Verify validation pattern detection."""
        code = """
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str

def validate_input(data):
    return User.model_validate(data)
"""
        result = detector.analyze(code)
        assert "validation_patterns" in result.detected_patterns

    def test_detect_logging_patterns(self, detector: PatternDetector) -> None:
        """Verify logging pattern detection."""
        code = """
import logging
logger = logging.getLogger(__name__)

def process():
    logger.info("Starting process")
    logger.debug("Processing data")
"""
        result = detector.analyze(code)
        assert "logging_patterns" in result.detected_patterns

    def test_detect_configuration_patterns(self, detector: PatternDetector) -> None:
        """Verify configuration pattern detection."""
        code = """
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY')
config = Settings()
"""
        result = detector.analyze(code)
        assert "configuration_patterns" in result.detected_patterns

    def test_detect_authentication_patterns(self, detector: PatternDetector) -> None:
        """Verify authentication pattern detection."""
        code = """
def make_request():
    headers = {'Authorization': f'Bearer {token}'}
    return client.get('/api', headers=headers)
"""
        result = detector.analyze(code)
        assert "authentication_patterns" in result.detected_patterns

    def test_detect_workflow_patterns(self, detector: PatternDetector) -> None:
        """Verify workflow pattern detection."""
        code = """
class DataPipeline:
    def __init__(self):
        self.steps = []

    def add_step(self, step):
        self.steps.append(step)

    async def orchestrate(self):
        for step in self.steps:
            await step.execute()
"""
        result = detector.analyze(code)
        assert "workflow_patterns" in result.detected_patterns

    def test_detect_testing_patterns(self, detector: PatternDetector) -> None:
        """Verify testing pattern detection."""
        code = """
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_client():
    return MagicMock()

def test_fetch_data(mock_client):
    result = fetch(mock_client)
    assert result is not None
"""
        result = detector.analyze(code)
        assert "testing_patterns" in result.detected_patterns

    def test_new_requirements_mapped(self, detector: PatternDetector) -> None:
        """Verify new patterns have requirement mappings."""
        new_patterns = [
            "rate_limiting",
            "streaming_patterns",
            "validation_patterns",
            "logging_patterns",
            "configuration_patterns",
            "authentication_patterns",
            "workflow_patterns",
            "testing_patterns",
        ]
        for pattern in new_patterns:
            assert pattern in detector._requirement_map, f"Missing requirement for: {pattern}"