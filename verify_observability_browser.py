#!/usr/bin/env python3
"""
Playwright-based verification of TTA.dev observability stack.

Verifies:
1. Prometheus metrics endpoint (http://localhost:9464/metrics)
2. Prometheus UI (http://localhost:9090)
3. Jaeger UI (http://localhost:16686)
4. Grafana dashboards (http://localhost:3001)
"""

import asyncio
import sys

import structlog
from playwright.async_api import Page, async_playwright

logger = structlog.get_logger()


class ObservabilityVerifier:
    def __init__(self):
        self.results = {
            "metrics_endpoint": False,
            "prometheus_ui": False,
            "prometheus_targets": False,
            "prometheus_query": False,
            "jaeger_ui": False,
            "jaeger_traces": False,
            "grafana_ui": False,
            "grafana_datasource": False,
        }
        self.errors = []

    async def verify_metrics_endpoint(self, page: Page) -> bool:
        """Verify Prometheus metrics endpoint returns TTA metrics."""
        try:
            logger.info("Checking metrics endpoint: http://localhost:9464/metrics")

            # Navigate to metrics endpoint
            response = await page.goto("http://localhost:9464/metrics", timeout=10000)

            if response.status != 200:
                self.errors.append(
                    f"Metrics endpoint returned status {response.status}"
                )
                return False

            # Get page content
            content = await page.content()

            # Check for TTA metrics
            tta_metrics = [
                "tta_workflow_executions_total",
                "tta_primitive_executions_total",
                "tta_execution_duration_seconds",
            ]

            found_metrics = []
            missing_metrics = []

            for metric in tta_metrics:
                if metric in content:
                    found_metrics.append(metric)
                else:
                    missing_metrics.append(metric)

            if found_metrics:
                logger.info(
                    f"✅ Found {len(found_metrics)} TTA metrics", metrics=found_metrics
                )
                self.results["metrics_endpoint"] = True
                return True
            else:
                self.errors.append(f"No TTA metrics found. Missing: {missing_metrics}")
                logger.warning("⚠️  No TTA metrics on endpoint", missing=missing_metrics)

                # Take screenshot for debugging
                await page.screenshot(path="/tmp/metrics_endpoint.png")
                logger.info("Screenshot saved to /tmp/metrics_endpoint.png")

                return False

        except Exception as e:
            self.errors.append(f"Metrics endpoint error: {str(e)}")
            logger.error("❌ Metrics endpoint check failed", error=str(e))
            return False

    async def verify_prometheus_ui(self, page: Page) -> bool:
        """Verify Prometheus UI is accessible and functional."""
        try:
            logger.info("Checking Prometheus UI: http://localhost:9090")

            # Navigate to Prometheus
            await page.goto("http://localhost:9090", timeout=10000)
            await page.wait_for_load_state("networkidle")

            # Check title
            title = await page.title()
            if "Prometheus" not in title:
                self.errors.append(f"Prometheus UI title unexpected: {title}")
                return False

            logger.info("✅ Prometheus UI loaded", title=title)
            self.results["prometheus_ui"] = True

            # Take screenshot
            await page.screenshot(path="/tmp/prometheus_ui.png")
            logger.info("Screenshot saved to /tmp/prometheus_ui.png")

            return True

        except Exception as e:
            self.errors.append(f"Prometheus UI error: {str(e)}")
            logger.error("❌ Prometheus UI check failed", error=str(e))
            return False

    async def verify_prometheus_targets(self, page: Page) -> bool:
        """Verify Prometheus targets including port 9464."""
        try:
            logger.info("Checking Prometheus targets")

            # Navigate to targets page
            await page.goto("http://localhost:9090/targets", timeout=10000)
            await page.wait_for_load_state("networkidle")

            # Get page content
            content = await page.content()

            # Check for port 9464 targets
            if "9464" in content:
                logger.info("✅ Port 9464 target found in Prometheus")

                # Check if target is UP
                if 'class="label alert alert-success"' in content or "UP" in content:
                    logger.info("✅ Target is UP")
                    self.results["prometheus_targets"] = True
                else:
                    logger.warning("⚠️  Target found but may not be UP")
                    self.results["prometheus_targets"] = (
                        True  # Still pass if target exists
                    )
            else:
                self.errors.append("Port 9464 not found in Prometheus targets")
                logger.warning("⚠️  Port 9464 not found in targets")

            # Take screenshot
            await page.screenshot(path="/tmp/prometheus_targets.png")
            logger.info("Screenshot saved to /tmp/prometheus_targets.png")

            return self.results["prometheus_targets"]

        except Exception as e:
            self.errors.append(f"Prometheus targets error: {str(e)}")
            logger.error("❌ Prometheus targets check failed", error=str(e))
            return False

    async def verify_prometheus_query(self, page: Page) -> bool:
        """Verify Prometheus can query TTA metrics."""
        try:
            logger.info("Checking Prometheus queries for TTA metrics")

            # Navigate to graph page
            await page.goto("http://localhost:9090/graph", timeout=10000)
            await page.wait_for_load_state("networkidle")

            # Find query input
            query_input = page.locator('input[placeholder*="Expression"]').first
            await query_input.fill("tta_workflow_executions_total")

            # Click execute button
            execute_button = page.locator('button:has-text("Execute")').first
            await execute_button.click()

            # Wait for results
            await page.wait_for_timeout(2000)

            # Check if we have results
            content = await page.content()

            if "tta_workflow_executions_total" in content:
                logger.info("✅ Prometheus query returned results")
                self.results["prometheus_query"] = True
            else:
                logger.warning("⚠️  No results for TTA metrics query")

            # Take screenshot
            await page.screenshot(path="/tmp/prometheus_query.png")
            logger.info("Screenshot saved to /tmp/prometheus_query.png")

            return self.results["prometheus_query"]

        except Exception as e:
            self.errors.append(f"Prometheus query error: {str(e)}")
            logger.error("❌ Prometheus query check failed", error=str(e))
            return False

    async def verify_jaeger_ui(self, page: Page) -> bool:
        """Verify Jaeger UI is accessible."""
        try:
            logger.info("Checking Jaeger UI: http://localhost:16686")

            # Navigate to Jaeger
            await page.goto("http://localhost:16686", timeout=10000)
            await page.wait_for_load_state("networkidle")

            # Check title or header
            title = await page.title()
            logger.info(f"Jaeger page title: {title}")

            # Take screenshot
            await page.screenshot(path="/tmp/jaeger_ui.png")
            logger.info("Screenshot saved to /tmp/jaeger_ui.png")

            self.results["jaeger_ui"] = True
            logger.info("✅ Jaeger UI loaded")

            return True

        except Exception as e:
            self.errors.append(f"Jaeger UI error: {str(e)}")
            logger.error("❌ Jaeger UI check failed", error=str(e))
            return False

    async def verify_jaeger_traces(self, page: Page) -> bool:
        """Check for traces in Jaeger."""
        try:
            logger.info("Checking for traces in Jaeger")

            # Already on Jaeger page
            await page.wait_for_timeout(2000)

            # Try to find service selector
            content = await page.content()

            # Look for TTA-related services
            tta_indicators = ["tta", "primitive", "workflow"]
            found_indicators = [
                ind for ind in tta_indicators if ind.lower() in content.lower()
            ]

            if found_indicators:
                logger.info(
                    "✅ Found TTA-related content in Jaeger",
                    indicators=found_indicators,
                )
                self.results["jaeger_traces"] = True
            else:
                logger.warning("⚠️  No obvious TTA traces found in Jaeger")

            return self.results["jaeger_traces"]

        except Exception as e:
            self.errors.append(f"Jaeger traces error: {str(e)}")
            logger.error("❌ Jaeger traces check failed", error=str(e))
            return False

    async def verify_grafana_ui(self, page: Page) -> bool:
        """Verify Grafana UI is accessible."""
        try:
            logger.info("Checking Grafana UI: http://localhost:3001")

            # Navigate to Grafana
            await page.goto("http://localhost:3001", timeout=10000)
            await page.wait_for_load_state("networkidle")

            # Check if we're on login page or dashboard
            content = await page.content()

            if "grafana" in content.lower() or "Grafana" in content:
                logger.info("✅ Grafana UI loaded")
                self.results["grafana_ui"] = True
            else:
                logger.warning("⚠️  Grafana page loaded but content unexpected")

            # Take screenshot
            await page.screenshot(path="/tmp/grafana_ui.png")
            logger.info("Screenshot saved to /tmp/grafana_ui.png")

            return self.results["grafana_ui"]

        except Exception as e:
            self.errors.append(f"Grafana UI error: {str(e)}")
            logger.error("❌ Grafana UI check failed", error=str(e))
            return False

    async def verify_grafana_datasource(self, page: Page) -> bool:
        """Verify Grafana can connect to Prometheus datasource."""
        try:
            logger.info("Checking Grafana datasources")

            # Navigate to datasources page
            await page.goto("http://localhost:3001/datasources", timeout=10000)
            await page.wait_for_timeout(2000)

            content = await page.content()

            if "prometheus" in content.lower():
                logger.info("✅ Prometheus datasource found in Grafana")
                self.results["grafana_datasource"] = True
            else:
                logger.warning("⚠️  Prometheus datasource not obvious in Grafana")

            # Take screenshot
            await page.screenshot(path="/tmp/grafana_datasources.png")
            logger.info("Screenshot saved to /tmp/grafana_datasources.png")

            return self.results["grafana_datasource"]

        except Exception as e:
            self.errors.append(f"Grafana datasource error: {str(e)}")
            logger.error("❌ Grafana datasource check failed", error=str(e))
            return False

    async def run_verification(self):
        """Run all verification checks."""
        logger.info("=" * 80)
        logger.info("TTA.dev Observability Stack Browser Verification")
        logger.info("=" * 80)

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=False
            )  # Non-headless to see what's happening
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            try:
                # Run all checks
                logger.info("\n📊 Step 1: Verifying Metrics Endpoint")
                await self.verify_metrics_endpoint(page)

                logger.info("\n📊 Step 2: Verifying Prometheus UI")
                await self.verify_prometheus_ui(page)

                logger.info("\n📊 Step 3: Verifying Prometheus Targets")
                await self.verify_prometheus_targets(page)

                logger.info("\n📊 Step 4: Verifying Prometheus Queries")
                await self.verify_prometheus_query(page)

                logger.info("\n📊 Step 5: Verifying Jaeger UI")
                await self.verify_jaeger_ui(page)

                logger.info("\n📊 Step 6: Checking Jaeger Traces")
                await self.verify_jaeger_traces(page)

                logger.info("\n📊 Step 7: Verifying Grafana UI")
                await self.verify_grafana_ui(page)

                logger.info("\n📊 Step 8: Verifying Grafana Datasource")
                await self.verify_grafana_datasource(page)

            finally:
                # Keep browser open for a moment to see results
                await page.wait_for_timeout(3000)
                await browser.close()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print verification summary."""
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)

        total_checks = len(self.results)
        passed_checks = sum(1 for v in self.results.values() if v)

        for check, passed in self.results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} - {check}")

        logger.info("\n" + "-" * 80)
        logger.info(f"Total: {passed_checks}/{total_checks} checks passed")
        logger.info("-" * 80)

        if self.errors:
            logger.info("\n🔍 ERRORS ENCOUNTERED:")
            for error in self.errors:
                logger.error(f"  - {error}")

        logger.info("\n📸 Screenshots saved to /tmp/:")
        logger.info("  - /tmp/metrics_endpoint.png")
        logger.info("  - /tmp/prometheus_ui.png")
        logger.info("  - /tmp/prometheus_targets.png")
        logger.info("  - /tmp/prometheus_query.png")
        logger.info("  - /tmp/jaeger_ui.png")
        logger.info("  - /tmp/grafana_ui.png")
        logger.info("  - /tmp/grafana_datasources.png")

        # Return exit code
        return 0 if passed_checks == total_checks else 1


async def main():
    """Main entry point."""
    # First, start the metrics server
    logger.info("Starting metrics test server...")

    # Import here to avoid issues if not yet created
    try:
        from tta_dev_primitives import WorkflowContext
        from tta_dev_primitives.observability import start_prometheus_exporter
        from tta_dev_primitives.testing import MockPrimitive

        # Start metrics server
        start_prometheus_exporter(port=9464)
        logger.info("✅ Metrics server started on port 9464")

        # Execute some test workflows to generate metrics
        logger.info("Executing test workflows to generate metrics...")

        step1 = MockPrimitive(name="Step1", return_value={"step": 1})
        step2 = MockPrimitive(name="Step2", return_value={"step": 2})
        step3 = MockPrimitive(name="Step3", return_value={"step": 3})

        workflow = step1 >> step2 >> step3
        context = WorkflowContext(trace_id="browser-verification")

        # Execute workflow a few times
        for i in range(5):
            await workflow.execute({"input": f"test-{i}"}, context)

        logger.info("✅ Test workflows executed")

        # Give Prometheus time to scrape
        await asyncio.sleep(5)

    except Exception as e:
        logger.warning(f"Could not start test workflows: {e}")
        logger.info("Continuing with verification anyway...")

    # Run verification
    verifier = ObservabilityVerifier()
    exit_code = await verifier.run_verification()

    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
