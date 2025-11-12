#!/usr/bin/env python3
"""
Long-running metrics server for verification.
Keeps the server running and executes workflows periodically.
"""

import asyncio
import sys

import structlog
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability.prometheus_exporter import start_http_server
from tta_dev_primitives.testing import MockPrimitive

logger = structlog.get_logger()


async def execute_test_workflows():
    """Execute test workflows to generate metrics."""
    # Create test primitives
    step1 = MockPrimitive(name="Step1", return_value={"step": 1})
    step2 = MockPrimitive(name="Step2", return_value={"step": 2})
    step3 = MockPrimitive(name="Step3", return_value={"step": 3})

    # Sequential workflow
    sequential = step1 >> step2 >> step3

    # Parallel workflow
    parallel = step1 | step2 | step3

    # Create context
    context = WorkflowContext(trace_id="metrics-server-test")

    try:
        # Execute sequential
        await sequential.execute({"input": "test"}, context)
        logger.info("✅ Sequential workflow executed")

        # Execute parallel
        await parallel.execute({"input": "test"}, context)
        logger.info("✅ Parallel workflow executed")

    except Exception as e:
        logger.error("Workflow execution failed", error=str(e))


async def main():
    """Main server loop."""
    logger.info("=" * 80)
    logger.info("TTA.dev Metrics Server - Long Running Mode")
    logger.info("=" * 80)

    # Start HTTP server
    logger.info("Starting Prometheus HTTP server on port 9464...")
    try:
        start_http_server(9464, addr="0.0.0.0")
        logger.info("✅ HTTP server started on http://0.0.0.0:9464/metrics")
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning("Port 9464 already in use - server may already be running")
        else:
            raise

    # Execute workflows immediately
    logger.info("Executing initial test workflows...")
    await execute_test_workflows()

    # Keep executing workflows periodically
    logger.info("Server running. Executing workflows every 30 seconds...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)

    try:
        while True:
            await asyncio.sleep(30)
            logger.info("Executing periodic workflows...")
            await execute_test_workflows()

    except KeyboardInterrupt:
        logger.info("\nShutting down metrics server...")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
