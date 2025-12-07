"""Tests for the TTA.dev CLI application."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tta_dev_primitives.cli.app import app


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_code_file(tmp_path: Path) -> Path:
    """Create a sample Python file for testing."""
    code = '''
async def fetch_data(url: str):
    """Fetch data from an API."""
    try:
        response = await client.get(url, timeout=30)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None
'''
    file_path = tmp_path / "sample.py"
    file_path.write_text(code)
    return file_path


@pytest.fixture
def complex_code_file(tmp_path: Path) -> Path:
    """Create a complex Python file with multiple patterns."""
    code = '''
import asyncio


async def robust_fetch(url: str, max_retries: int = 3):
    """Fetch with retry logic."""
    for attempt in range(max_retries):
        try:
            result = await asyncio.wait_for(
                client.get(url),
                timeout=30
            )
            return result.json()
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
        except Exception:
            return await fallback_fetch(url)


async def parallel_fetch(urls: list[str]):
    """Fetch multiple URLs in parallel."""
    return await asyncio.gather(*[fetch(url) for url in urls])
'''
    file_path = tmp_path / "complex.py"
    file_path.write_text(code)
    return file_path


class TestCLIHelp:
    """Tests for CLI help and basic functionality."""

    def test_help(self, runner: CliRunner) -> None:
        """Verify --help works."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "TTA.dev" in result.stdout

    def test_no_args_shows_help(self, runner: CliRunner) -> None:
        """Verify no args shows help."""
        result = runner.invoke(app, [])
        # Exit code 0 or 2 are both acceptable (2 is normal for no_args_is_help)
        assert result.exit_code in [0, 2]
        assert "Usage" in result.stdout


class TestVersionCommand:
    """Tests for the version command."""

    def test_version(self, runner: CliRunner) -> None:
        """Verify version command works."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "TTA.dev" in result.stdout
        assert "v" in result.stdout


class TestAnalyzeCommand:
    """Tests for the analyze command."""

    def test_analyze_help(self, runner: CliRunner) -> None:
        """Verify analyze --help works."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "Analyze" in result.stdout

    def test_analyze_file(self, runner: CliRunner, sample_code_file: Path) -> None:
        """Verify analyze command works on a file."""
        result = runner.invoke(app, ["analyze", str(sample_code_file)])
        assert result.exit_code == 0
        # Should show analysis results
        assert "Analysis" in result.stdout or "Recommendations" in result.stdout

    def test_analyze_detects_patterns(
        self, runner: CliRunner, sample_code_file: Path
    ) -> None:
        """Verify analyze detects patterns."""
        result = runner.invoke(app, ["analyze", str(sample_code_file)])
        assert result.exit_code == 0
        # Should detect async and error handling
        output = result.stdout.lower()
        assert "async" in output or "pattern" in output

    def test_analyze_json_output(
        self, runner: CliRunner, sample_code_file: Path
    ) -> None:
        """Verify analyze --output json works."""
        result = runner.invoke(
            app, ["analyze", str(sample_code_file), "--output", "json"]
        )
        assert result.exit_code == 0
        # Extract JSON from output (may have log lines before it)
        output = result.stdout
        json_start = output.find("{")
        assert json_start >= 0, "No JSON found in output"
        data = json.loads(output[json_start:])
        assert "analysis" in data
        assert "recommendations" in data

    def test_analyze_brief_output(
        self, runner: CliRunner, sample_code_file: Path
    ) -> None:
        """Verify analyze --output brief works."""
        result = runner.invoke(
            app, ["analyze", str(sample_code_file), "--output", "brief"]
        )
        assert result.exit_code == 0

    def test_analyze_with_templates(
        self, runner: CliRunner, sample_code_file: Path
    ) -> None:
        """Verify analyze --templates shows code templates."""
        result = runner.invoke(app, ["analyze", str(sample_code_file), "--templates"])
        assert result.exit_code == 0
        # Should show template code
        output = result.stdout
        assert "from tta_dev_primitives" in output or "Template" in output

    def test_analyze_min_confidence(
        self, runner: CliRunner, sample_code_file: Path
    ) -> None:
        """Verify analyze --min-confidence works."""
        result = runner.invoke(
            app,
            ["analyze", str(sample_code_file), "--min-confidence", "0.8"],
        )
        assert result.exit_code == 0

    def test_analyze_nonexistent_file(self, runner: CliRunner) -> None:
        """Verify analyze handles nonexistent file."""
        result = runner.invoke(app, ["analyze", "/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_analyze_complex_file(
        self, runner: CliRunner, complex_code_file: Path
    ) -> None:
        """Verify analyze works on complex code."""
        result = runner.invoke(app, ["analyze", str(complex_code_file)])
        assert result.exit_code == 0
        # Should detect multiple patterns
        output = result.stdout.lower()
        assert "primitive" in output or "recommendation" in output

    def test_analyze_quiet_flag(
        self, runner: CliRunner, sample_code_file: Path
    ) -> None:
        """Verify --quiet suppresses debug logs."""
        result = runner.invoke(app, ["analyze", str(sample_code_file), "--quiet"])
        assert result.exit_code == 0
        # Should not have debug logs
        assert "[debug]" not in result.stdout.lower()

    def test_analyze_lines_flag(
        self, runner: CliRunner, complex_code_file: Path
    ) -> None:
        """Verify --lines shows line numbers for issues."""
        result = runner.invoke(
            app, ["analyze", str(complex_code_file), "--lines", "--quiet"]
        )
        assert result.exit_code == 0
        # Should show line numbers in issues/opportunities
        output = result.stdout
        # Line numbers appear as "(lines: X, Y, Z)"
        assert "lines:" in output.lower() or "line" in output.lower()

    def test_analyze_suggest_diff_flag(
        self, runner: CliRunner, complex_code_file: Path
    ) -> None:
        """Verify --suggest-diff shows transformation suggestions."""
        result = runner.invoke(
            app, ["analyze", str(complex_code_file), "--suggest-diff", "--quiet"]
        )
        assert result.exit_code == 0
        # Should show suggested transformations
        output = result.stdout
        assert "Suggested" in output or "suggestion" in output.lower()

    def test_analyze_json_with_lines(
        self, runner: CliRunner, complex_code_file: Path
    ) -> None:
        """Verify JSON output includes line_info when --lines is used."""
        result = runner.invoke(
            app,
            [
                "analyze",
                str(complex_code_file),
                "--output",
                "json",
                "--lines",
                "--quiet",
            ],
        )
        assert result.exit_code == 0
        # Extract JSON
        output = result.stdout
        json_start = output.find("{")
        assert json_start >= 0
        data = json.loads(output[json_start:])
        # Should have line_info
        assert "line_info" in data


class TestPrimitivesCommand:
    """Tests for the primitives command."""

    def test_primitives_help(self, runner: CliRunner) -> None:
        """Verify primitives --help works."""
        result = runner.invoke(app, ["primitives", "--help"])
        assert result.exit_code == 0

    def test_primitives_list(self, runner: CliRunner) -> None:
        """Verify primitives command lists primitives."""
        result = runner.invoke(app, ["primitives"])
        assert result.exit_code == 0
        # Should list known primitives
        assert "RetryPrimitive" in result.stdout
        assert "TimeoutPrimitive" in result.stdout
        assert "CachePrimitive" in result.stdout

    def test_primitives_shows_descriptions(self, runner: CliRunner) -> None:
        """Verify primitives shows descriptions."""
        result = runner.invoke(app, ["primitives"])
        assert result.exit_code == 0
        # Should have descriptions
        output = result.stdout.lower()
        assert "retry" in output or "timeout" in output or "cache" in output


class TestDocsCommand:
    """Tests for the docs command."""

    def test_docs_help(self, runner: CliRunner) -> None:
        """Verify docs --help works."""
        result = runner.invoke(app, ["docs", "--help"])
        assert result.exit_code == 0

    def test_docs_retry_primitive(self, runner: CliRunner) -> None:
        """Verify docs shows RetryPrimitive info."""
        result = runner.invoke(app, ["docs", "RetryPrimitive"])
        assert result.exit_code == 0
        assert "RetryPrimitive" in result.stdout
        # Should show import
        assert "from tta_dev_primitives" in result.stdout

    def test_docs_timeout_primitive(self, runner: CliRunner) -> None:
        """Verify docs shows TimeoutPrimitive info."""
        result = runner.invoke(app, ["docs", "TimeoutPrimitive"])
        assert result.exit_code == 0
        assert "Timeout" in result.stdout

    def test_docs_cache_primitive(self, runner: CliRunner) -> None:
        """Verify docs shows CachePrimitive info."""
        result = runner.invoke(app, ["docs", "CachePrimitive"])
        assert result.exit_code == 0
        assert "Cache" in result.stdout

    def test_docs_shows_use_cases(self, runner: CliRunner) -> None:
        """Verify docs shows use cases."""
        result = runner.invoke(app, ["docs", "RetryPrimitive"])
        assert result.exit_code == 0
        # Should show use cases
        output = result.stdout.lower()
        assert "use" in output or "case" in output or "api" in output

    def test_docs_shows_template(self, runner: CliRunner) -> None:
        """Verify docs shows code template."""
        result = runner.invoke(app, ["docs", "RetryPrimitive"])
        assert result.exit_code == 0
        # Should show code template
        assert "from tta_dev_primitives" in result.stdout

    def test_docs_all_templates(self, runner: CliRunner) -> None:
        """Verify docs --all shows all templates."""
        result = runner.invoke(app, ["docs", "RetryPrimitive", "--all"])
        assert result.exit_code == 0

    def test_docs_unknown_primitive(self, runner: CliRunner) -> None:
        """Verify docs handles unknown primitive."""
        result = runner.invoke(app, ["docs", "UnknownPrimitive"])
        # Should either exit with error or show not found message
        assert result.exit_code != 0 or "not found" in result.stdout.lower()


class TestServeCommand:
    """Tests for the serve command."""

    def test_serve_help(self, runner: CliRunner) -> None:
        """Verify serve --help works."""
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "MCP" in result.stdout or "server" in result.stdout.lower()

    def test_serve_shows_transport_option(self, runner: CliRunner) -> None:
        """Verify serve shows transport option."""
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "transport" in result.stdout.lower()

    def test_serve_shows_port_option(self, runner: CliRunner) -> None:
        """Verify serve shows port option."""
        result = runner.invoke(app, ["serve", "--help"])
        assert result.exit_code == 0
        assert "port" in result.stdout.lower()


class TestCLIIntegration:
    """Integration tests for CLI workflows."""

    def _extract_json(self, output: str) -> dict:
        """Extract JSON from output that may have log lines."""
        json_start = output.find("{")
        if json_start < 0:
            raise ValueError("No JSON found in output")
        return json.loads(output[json_start:])

    def test_analyze_then_docs(self, runner: CliRunner, sample_code_file: Path) -> None:
        """Verify workflow: analyze -> docs."""
        # First analyze
        analyze_result = runner.invoke(
            app, ["analyze", str(sample_code_file), "--output", "json"]
        )
        assert analyze_result.exit_code == 0

        # Parse recommendations
        data = self._extract_json(analyze_result.stdout)
        if data["recommendations"]:
            primitive = data["recommendations"][0]["primitive_name"]
            # Then get docs for that primitive
            docs_result = runner.invoke(app, ["docs", primitive])
            assert docs_result.exit_code == 0
            assert primitive in docs_result.stdout

    def test_json_output_is_parseable(
        self, runner: CliRunner, complex_code_file: Path
    ) -> None:
        """Verify JSON output is always valid."""
        result = runner.invoke(
            app, ["analyze", str(complex_code_file), "--output", "json"]
        )
        assert result.exit_code == 0

        # Should parse without error
        data = self._extract_json(result.stdout)
        assert isinstance(data, dict)
        assert "analysis" in data
        assert "detected_patterns" in data["analysis"]

    def test_recommendations_have_required_fields(
        self, runner: CliRunner, complex_code_file: Path
    ) -> None:
        """Verify recommendations have required fields."""
        result = runner.invoke(
            app, ["analyze", str(complex_code_file), "--output", "json"]
        )
        assert result.exit_code == 0

        data = self._extract_json(result.stdout)
        for rec in data["recommendations"]:
            assert "primitive_name" in rec
            assert "confidence_score" in rec
            assert "reasoning" in rec


class TestBenchmarkCommand:
    """Tests for the benchmark command."""

    def test_benchmark_help(self, runner: CliRunner) -> None:
        """Verify benchmark --help works."""
        result = runner.invoke(app, ["benchmark", "--help"])
        assert result.exit_code == 0
        assert "benchmark" in result.stdout.lower()
        assert "ACE" in result.stdout or "learning" in result.stdout.lower()

    def test_benchmark_shows_options(self, runner: CliRunner) -> None:
        """Verify benchmark command shows all options."""
        result = runner.invoke(app, ["benchmark", "--help"])
        assert result.exit_code == 0
        assert "--difficulty" in result.stdout
        assert "--output" in result.stdout
        assert "--iterations" in result.stdout

    def test_benchmark_without_e2b_key_fails_gracefully(
        self, runner: CliRunner, monkeypatch
    ) -> None:
        """Verify benchmark handles missing E2B key gracefully."""
        # Remove E2B keys from environment
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        monkeypatch.delenv("E2B_KEY", raising=False)

        result = runner.invoke(app, ["benchmark", "--difficulty", "easy"])
        # Should fail but not crash
        assert result.exit_code == 1
        assert "E2B" in result.stdout or "API key" in result.stdout.lower()


class TestABTestCommand:
    """Tests for the ab-test command."""

    def test_ab_test_help(self, runner: CliRunner) -> None:
        """Verify ab-test --help works."""
        result = runner.invoke(app, ["ab-test", "--help"])
        assert result.exit_code == 0
        assert "A/B" in result.stdout or "test" in result.stdout.lower()

    def test_ab_test_shows_options(self, runner: CliRunner) -> None:
        """Verify ab-test command shows all options."""
        result = runner.invoke(app, ["ab-test", "--help"])
        assert result.exit_code == 0
        assert "--variants" in result.stdout
        assert "--runs" in result.stdout
        assert "--output" in result.stdout

    def test_ab_test_requires_file(self, runner: CliRunner) -> None:
        """Verify ab-test requires a file argument."""
        result = runner.invoke(app, ["ab-test"])
        # Should show error about missing file
        assert result.exit_code != 0

    def test_ab_test_without_e2b_key_fails_gracefully(
        self, runner: CliRunner, sample_code_file: Path, monkeypatch
    ) -> None:
        """Verify ab-test handles missing E2B key gracefully."""
        # Remove E2B keys from environment
        monkeypatch.delenv("E2B_API_KEY", raising=False)
        monkeypatch.delenv("E2B_KEY", raising=False)

        result = runner.invoke(app, ["ab-test", str(sample_code_file)])
        # Should fail but not crash
        assert result.exit_code == 1
        assert "E2B" in result.stdout or "API key" in result.stdout.lower()

    def test_ab_test_file_not_found(self, runner: CliRunner) -> None:
        """Verify ab-test handles non-existent file."""
        result = runner.invoke(app, ["ab-test", "nonexistent_file.py"])
        assert result.exit_code != 0
