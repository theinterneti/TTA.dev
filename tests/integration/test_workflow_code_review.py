"""
Multi-package workflow test: Code Analysis and Review Pipeline.

Demonstrates:
- Sequential code analysis stages
- Parallel quality checks
- Observable primitives for monitoring
- Context-aware processing
- Real-world code review scenario
"""

import asyncio

import pytest
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.observability.tracing import ObservablePrimitive


# ============================================================================
# Code Analysis Primitives
# ============================================================================


class SyntaxChecker(WorkflowPrimitive[dict, dict]):
    """Check code syntax."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze syntax."""
        await asyncio.sleep(0.01)
        code = input_data.get("code", "")
        
        # Simple syntax check (mock)
        has_errors = "import" not in code and len(code) > 0
        
        return {
            **input_data,
            "syntax_checked": True,
            "syntax_errors": 1 if has_errors else 0,
            "stage": "syntax",
        }


class StyleChecker(WorkflowPrimitive[dict, dict]):
    """Check code style."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze style."""
        await asyncio.sleep(0.01)
        code = input_data.get("code", "")
        
        # Simple style check (mock)
        style_issues = len(code) // 100  # 1 issue per 100 chars
        
        return {
            **input_data,
            "style_checked": True,
            "style_issues": style_issues,
            "stage": "style",
        }


class SecurityChecker(WorkflowPrimitive[dict, dict]):
    """Check for security issues."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze security."""
        await asyncio.sleep(0.02)
        code = input_data.get("code", "")
        
        # Simple security check (mock)
        security_warnings = 1 if "eval" in code or "exec" in code else 0
        
        return {
            **input_data,
            "security_checked": True,
            "security_warnings": security_warnings,
            "stage": "security",
        }


class ComplexityAnalyzer(WorkflowPrimitive[dict, dict]):
    """Analyze code complexity."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze complexity."""
        await asyncio.sleep(0.01)
        code = input_data.get("code", "")
        
        # Simple complexity calculation (mock)
        lines = code.count("\n") + 1
        complexity = min(lines // 10, 10)  # 1-10 scale
        
        return {
            **input_data,
            "complexity_analyzed": True,
            "complexity_score": complexity,
            "lines_of_code": lines,
        }


class ReviewSummarizer(WorkflowPrimitive[list, dict]):
    """Summarize code review results."""

    async def execute(self, input_data: list, context: WorkflowContext) -> dict:
        """Summarize results from all checkers."""
        total_issues = 0
        stages = []
        
        for result in input_data:
            if isinstance(result, dict):
                stages.append(result.get("stage", "unknown"))
                total_issues += result.get("syntax_errors", 0)
                total_issues += result.get("style_issues", 0)
                total_issues += result.get("security_warnings", 0)
        
        return {
            "summary": "code_review_complete",
            "stages_completed": stages,
            "total_issues": total_issues,
            "review_passed": total_issues == 0,
        }


# ============================================================================
# Tests: Basic Code Analysis
# ============================================================================


@pytest.mark.asyncio
async def test_syntax_check():
    """Test basic syntax checking."""
    checker = SyntaxChecker()
    context = WorkflowContext(workflow_id="syntax-test")
    
    result = await checker.execute({"code": "import os\nprint('hello')"}, context)
    
    assert result["syntax_checked"] is True
    assert result["syntax_errors"] == 0


@pytest.mark.asyncio
async def test_style_check():
    """Test style checking."""
    checker = StyleChecker()
    context = WorkflowContext(workflow_id="style-test")
    
    # Long code should have style issues
    long_code = "x = 1\n" * 150  # 300+ chars
    result = await checker.execute({"code": long_code}, context)
    
    assert result["style_checked"] is True
    assert result["style_issues"] > 0


@pytest.mark.asyncio
async def test_security_check():
    """Test security checking."""
    checker = SecurityChecker()
    context = WorkflowContext(workflow_id="security-test")
    
    # Code with security issue
    result = await checker.execute({"code": "eval(user_input)"}, context)
    assert result["security_warnings"] > 0
    
    # Safe code
    result = await checker.execute({"code": "print('safe')"}, context)
    assert result["security_warnings"] == 0


@pytest.mark.asyncio
async def test_complexity_analysis():
    """Test complexity analysis."""
    analyzer = ComplexityAnalyzer()
    context = WorkflowContext(workflow_id="complexity-test")
    
    # Simple code
    simple_code = "print('hello')"
    result = await analyzer.execute({"code": simple_code}, context)
    assert result["complexity_score"] == 0  # Very simple
    
    # Complex code
    complex_code = "\n".join(["def func():", "    pass"] * 50)  # 100 lines
    result = await analyzer.execute({"code": complex_code}, context)
    assert result["complexity_score"] >= 5  # More complex


# ============================================================================
# Tests: Sequential Review Pipeline
# ============================================================================


@pytest.mark.asyncio
async def test_sequential_review_pipeline():
    """Test sequential code review stages."""
    syntax = SyntaxChecker()
    style = StyleChecker()
    security = SecurityChecker()
    complexity = ComplexityAnalyzer()
    
    # Build pipeline
    pipeline = syntax >> style >> security >> complexity
    
    # Execute
    context = WorkflowContext(workflow_id="sequential-review")
    code = "import os\nimport sys\nprint('test')"
    result = await pipeline.execute({"code": code}, context)
    
    # All checks should be done
    assert result["syntax_checked"] is True
    assert result["style_checked"] is True
    assert result["security_checked"] is True
    assert result["complexity_analyzed"] is True


@pytest.mark.asyncio
async def test_observable_review_pipeline():
    """Test review pipeline with observability."""
    syntax = ObservablePrimitive(SyntaxChecker(), name="syntax")
    style = ObservablePrimitive(StyleChecker(), name="style")
    
    pipeline = syntax >> style
    
    context = WorkflowContext(workflow_id="observable-review", correlation_id="review-123")
    result = await pipeline.execute({"code": "import test"}, context)
    
    assert result["syntax_checked"] is True
    assert result["style_checked"] is True
    assert context.correlation_id == "review-123"


# ============================================================================
# Tests: Parallel Quality Checks
# ============================================================================


@pytest.mark.asyncio
async def test_parallel_quality_checks():
    """Test running multiple checks in parallel."""
    syntax = SyntaxChecker()
    style = StyleChecker()
    security = SecurityChecker()
    
    # Run all checks in parallel
    parallel_checks = ParallelPrimitive([syntax, style, security])
    
    context = WorkflowContext(workflow_id="parallel-checks")
    code = "import os\neval(input())\n" + "x = 1\n" * 50
    results = await parallel_checks.execute({"code": code}, context)
    
    # Should have results from all 3 checkers
    assert len(results) == 3
    stages = {r.get("stage") for r in results}
    assert "syntax" in stages
    assert "style" in stages
    assert "security" in stages


@pytest.mark.asyncio
async def test_parallel_with_summarizer():
    """Test parallel checks followed by summarization."""
    syntax = SyntaxChecker()
    style = StyleChecker()
    security = SecurityChecker()
    
    parallel_checks = ParallelPrimitive([syntax, style, security])
    summarizer = ReviewSummarizer()
    
    # Build workflow
    workflow = parallel_checks >> summarizer
    
    context = WorkflowContext(workflow_id="parallel-summary")
    code = "import os\nprint('safe code')"
    result = await workflow.execute({"code": code}, context)
    
    # Should have summary
    assert result["summary"] == "code_review_complete"
    assert len(result["stages_completed"]) == 3
    assert isinstance(result["total_issues"], int)


# ============================================================================
# Tests: Complete Review Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_complete_code_review_workflow():
    """Test complete code review workflow with all stages."""
    # Stage 1: Syntax check (must pass first)
    syntax = ObservablePrimitive(SyntaxChecker(), name="syntax_check")
    
    # Stage 2: Parallel quality checks
    style = ObservablePrimitive(StyleChecker(), name="style_check")
    security = ObservablePrimitive(SecurityChecker(), name="security_check")
    complexity = ObservablePrimitive(ComplexityAnalyzer(), name="complexity_analysis")
    
    parallel_quality = ParallelPrimitive([style, security, complexity])
    
    # Stage 3: Summarize
    summarizer = ObservablePrimitive(ReviewSummarizer(), name="summarizer")
    
    # Build complete workflow
    workflow = syntax >> parallel_quality >> summarizer
    
    # Execute with good code
    context = WorkflowContext(workflow_id="complete-review", correlation_id="rev-456")
    code = "import os\nimport sys\n\ndef main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()"
    
    result = await workflow.execute({"code": code}, context)
    
    # Verify complete review
    assert result["summary"] == "code_review_complete"
    assert len(result["stages_completed"]) == 3
    # Good code should pass
    assert result["review_passed"] is True or result["total_issues"] <= 1


@pytest.mark.asyncio
async def test_review_workflow_with_issues():
    """Test code review workflow detecting issues."""
    syntax = SyntaxChecker()
    style = StyleChecker()
    security = SecurityChecker()
    
    parallel = ParallelPrimitive([syntax, style, security])
    summarizer = ReviewSummarizer()
    
    workflow = parallel >> summarizer
    
    # Code with multiple issues
    context = WorkflowContext(workflow_id="review-with-issues")
    bad_code = "eval(input())\n" * 10 + "x=1\n" * 200  # Security + style issues
    
    result = await workflow.execute({"code": bad_code}, context)
    
    # Should detect issues
    assert result["total_issues"] > 0
    assert result["review_passed"] is False


# ============================================================================
# Tests: Context-Aware Processing
# ============================================================================


@pytest.mark.asyncio
async def test_context_metadata_in_review():
    """Test that review workflow uses context metadata."""
    
    class ContextAwareChecker(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            # Use context to customize checking
            strict_mode = context.metadata.get("strict_mode", False)
            threshold = 0 if strict_mode else 5
            
            issues = len(input_data.get("code", "")) // 50
            
            return {
                **input_data,
                "issues_found": issues,
                "failed": issues > threshold,
                "strict_mode": strict_mode,
            }
    
    checker = ContextAwareChecker()
    
    # Normal mode
    context = WorkflowContext(workflow_id="context-aware")
    context.metadata["strict_mode"] = False
    result = await checker.execute({"code": "x" * 300}, context)
    assert result["failed"] is True  # 6 issues > 5 threshold
    
    # Strict mode
    context.metadata["strict_mode"] = True
    result = await checker.execute({"code": "x" * 10}, context)
    assert result["failed"] is False  # 0 issues in strict mode


@pytest.mark.asyncio
async def test_review_pipeline_performance():
    """Test that parallel review is faster than sequential."""
    import time
    
    # Sequential
    seq_workflow = SyntaxChecker() >> StyleChecker() >> SecurityChecker()
    context = WorkflowContext(workflow_id="seq-perf")
    
    start = time.time()
    await seq_workflow.execute({"code": "test"}, context)
    seq_duration = time.time() - start
    
    # Parallel
    par_workflow = ParallelPrimitive([SyntaxChecker(), StyleChecker(), SecurityChecker()])
    context = WorkflowContext(workflow_id="par-perf")
    
    start = time.time()
    await par_workflow.execute({"code": "test"}, context)
    par_duration = time.time() - start
    
    # Parallel should be faster
    assert par_duration < seq_duration * 0.7


@pytest.mark.asyncio
async def test_large_codebase_review():
    """Test review workflow with large codebase."""
    # Simulate reviewing multiple files in parallel
    files = [
        {"code": f"import file{i}\ndef func{i}(): pass", "filename": f"file{i}.py"}
        for i in range(5)
    ]
    
    checker = SyntaxChecker()
    
    # Review all files in parallel
    parallel_review = ParallelPrimitive([checker] * len(files))
    
    context = WorkflowContext(workflow_id="large-review")
    results = await parallel_review.execute(files[0], context)  # Using same input for simplicity
    
    # Should complete all reviews
    assert len(results) == 5
    assert all(r["syntax_checked"] for r in results)
