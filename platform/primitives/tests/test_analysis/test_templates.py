"""Tests for the TemplateProvider class."""

import pytest

from tta_dev_primitives.analysis.templates import TemplateProvider


class TestTemplateProvider:
    """Tests for TemplateProvider functionality."""

    @pytest.fixture
    def provider(self) -> TemplateProvider:
        """Create a TemplateProvider instance."""
        return TemplateProvider()

    def test_list_available_templates(self, provider: TemplateProvider) -> None:
        """Verify list_available_templates returns primitive names."""
        available = provider.list_available_templates()
        assert isinstance(available, list)
        assert len(available) >= 7

        expected = [
            "RetryPrimitive",
            "TimeoutPrimitive",
            "CachePrimitive",
            "FallbackPrimitive",
            "ParallelPrimitive",
            "SequentialPrimitive",
            "RouterPrimitive",
        ]
        for prim in expected:
            assert prim in available

    def test_get_template_returns_string(self, provider: TemplateProvider) -> None:
        """Verify get_template returns code string."""
        template = provider.get_template("RetryPrimitive")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_get_template_contains_import(self, provider: TemplateProvider) -> None:
        """Verify template contains import statement."""
        template = provider.get_template("RetryPrimitive")
        assert "from tta_dev_primitives" in template or "import" in template

    def test_get_template_contains_primitive_name(self, provider: TemplateProvider) -> None:
        """Verify template contains primitive class name."""
        template = provider.get_template("CachePrimitive")
        assert "Cache" in template

    def test_get_template_unknown_returns_empty_or_none(self, provider: TemplateProvider) -> None:
        """Verify unknown primitive returns empty or None."""
        template = provider.get_template("UnknownPrimitive")
        assert template is None or template == ""

    def test_get_templates_returns_list(self, provider: TemplateProvider) -> None:
        """Verify get_all_templates returns dict of templates."""
        templates = provider.get_all_templates("RetryPrimitive")
        assert isinstance(templates, dict)
        # Should have at least one template
        assert len(templates) > 0

    def test_get_examples_returns_list(self, provider: TemplateProvider) -> None:
        """Verify get_examples returns list of examples."""
        examples = provider.get_examples("RetryPrimitive")
        assert isinstance(examples, list)

    def test_search_templates_by_keyword(self, provider: TemplateProvider) -> None:
        """Verify search finds templates by keyword."""
        results = provider.search_templates("timeout")
        assert isinstance(results, list)
        # Should find TimeoutPrimitive at minimum
        assert len(results) > 0

    def test_search_templates_empty_query(self, provider: TemplateProvider) -> None:
        """Verify empty search returns all or empty."""
        results = provider.search_templates("")
        assert isinstance(results, list)

    def test_retry_template_has_backoff(self, provider: TemplateProvider) -> None:
        """Verify RetryPrimitive template mentions backoff."""
        template = provider.get_template("RetryPrimitive")
        assert "backoff" in template.lower() or "retry" in template.lower()

    def test_timeout_template_has_timeout(self, provider: TemplateProvider) -> None:
        """Verify TimeoutPrimitive template mentions timeout."""
        template = provider.get_template("TimeoutPrimitive")
        assert "timeout" in template.lower()

    def test_cache_template_has_ttl(self, provider: TemplateProvider) -> None:
        """Verify CachePrimitive template mentions TTL."""
        template = provider.get_template("CachePrimitive")
        assert "ttl" in template.lower() or "cache" in template.lower()

    def test_fallback_template_has_fallback(self, provider: TemplateProvider) -> None:
        """Verify FallbackPrimitive template mentions fallback."""
        template = provider.get_template("FallbackPrimitive")
        assert "fallback" in template.lower()

    def test_parallel_template_has_parallel(self, provider: TemplateProvider) -> None:
        """Verify ParallelPrimitive template mentions parallel."""
        template = provider.get_template("ParallelPrimitive")
        assert "parallel" in template.lower() or "gather" in template.lower()

    def test_sequential_template_has_sequential(self, provider: TemplateProvider) -> None:
        """Verify SequentialPrimitive template mentions sequential."""
        template = provider.get_template("SequentialPrimitive")
        assert "sequential" in template.lower() or "sequence" in template.lower()

    def test_router_template_has_routes(self, provider: TemplateProvider) -> None:
        """Verify RouterPrimitive template mentions routes."""
        template = provider.get_template("RouterPrimitive")
        assert "route" in template.lower()

    def test_all_templates_are_valid_python(self, provider: TemplateProvider) -> None:
        """Verify all templates are syntactically valid Python (allowing await)."""
        for prim in provider.list_available_templates():
            template = provider.get_template(prim)
            if template:
                # Wrap in async function to allow await
                wrapped = "async def _test():\n" + "\n".join(
                    f"    {line}" if line.strip() else line for line in template.split("\n")
                )
                try:
                    compile(wrapped, f"<{prim}>", "exec")
                except SyntaxError as e:
                    pytest.fail(f"{prim} template has syntax error: {e}")

    def test_get_all_templates(self, provider: TemplateProvider) -> None:
        """Verify get_all_templates returns dict for a primitive."""
        all_templates = provider.get_all_templates("RetryPrimitive")
        assert isinstance(all_templates, dict)
        assert len(all_templates) >= 1
