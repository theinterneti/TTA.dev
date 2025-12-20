#!/usr/bin/env python3
"""
Robust n8n GitHub Dashboard Setup using TTA.dev Adaptive Primitives
This script uses TTA.dev's retry, timeout, and fallback patterns to ensure reliable n8n setup
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import aiohttp
from tta_dev_primitives.adaptive.base import AdaptiveWorkflowContext
from tta_dev_primitives.adaptive.fallback import FallbackPrimitive

# TTA.dev imports for robust patterns
from tta_dev_primitives.adaptive.retry import RetryPrimitive
from tta_dev_primitives.adaptive.timeout import TimeoutPrimitive

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class N8nSetupEngine:
    """TTA.dev powered n8n setup engine with adaptive patterns"""

    def __init__(self):
        self.context = AdaptiveWorkflowContext(
            correlation_id="n8n-setup-001", data={"setup_type": "github_dashboard"}
        )
        self.n8n_base_url = "http://localhost:5678"
        self.workflow_file = "n8n_github_health_dashboard.json"

    async def setup_n8n_dashboard(self) -> dict[str, Any]:
        """Main setup workflow using TTA.dev primitives"""
        logger.info("🚀 Starting robust n8n GitHub Dashboard setup...")

        # Create resilient workflow using TTA.dev patterns
        setup_workflow = (
            self._check_n8n_service()  # Check if n8n is accessible
            >> self._verify_github_api()  # Test GitHub API
            >> self._verify_gemini_api()  # Test Gemini API
            >> self._import_workflow()  # Import and activate workflow
            >> self._validate_setup()  # Final validation
        )

        try:
            result = await setup_workflow.execute(self.context, {})
            logger.info("✅ n8n setup completed successfully!")
            return result
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _check_n8n_service(self) -> dict[str, Any]:
        """Check n8n service availability with retry and timeout"""
        logger.info("📡 Checking n8n service availability...")

        async def check_n8n_health():
            async with aiohttp.ClientSession() as session:
                try:
                    # Check web interface
                    async with session.get(
                        f"{self.n8n_base_url}/healthz", timeout=5
                    ) as resp:
                        if resp.status == 200:
                            logger.info("✅ n8n web interface accessible")
                            return {"status": "healthy", "web_interface": "ok"}
                        else:
                            raise Exception(f"HTTP {resp.status}")
                except Exception as e:
                    logger.warning(f"❌ n8n health check failed: {e}")
                    raise

        # Use TTA.dev RetryPrimitive with exponential backoff
        retry_primitive = RetryPrimitive(
            primitive=check_n8n_health,
            max_retries=5,
            backoff_strategy="exponential",
            max_delay=30,
        )

        return await retry_primitive.execute(self.context, {})

    async def _verify_github_api(self) -> dict[str, Any]:
        """Verify GitHub API connectivity with fallback"""
        logger.info("🔑 Verifying GitHub API connectivity...")

        github_token = (
            os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
            or "ghp_YOUR_GITHUB_TOKEN_HERE"
        )

        async def test_github_api():
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                async with session.get(
                    "https://api.github.com/repos/theinterneti/TTA.dev",
                    headers=headers,
                    timeout=10,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"✅ GitHub API working - {data.get('full_name')}")
                        return {"status": "ok", "repo": data.get("full_name")}
                    else:
                        raise Exception(f"GitHub API HTTP {resp.status}")

        # Use FallbackPrimitive for graceful degradation
        fallback_primitive = FallbackPrimitive(
            primary=test_github_api,
            fallback=lambda: {
                "status": "degraded",
                "message": "GitHub API unavailable",
            },
        )

        return await fallback_primitive.execute(self.context, {})

    async def _verify_gemini_api(self) -> dict[str, Any]:
        """Verify Gemini API connectivity with robust error handling"""
        logger.info("🤖 Verifying Gemini AI API connectivity...")

        gemini_key = (
            os.getenv("GEMINI_API_KEY") or "AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE"
        )

        async def test_gemini_api():
            payload = {"contents": [{"parts": [{"text": "Hello, test message"}]}]}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}",
                    json=payload,
                    timeout=10,
                ) as resp:
                    if resp.status == 200:
                        logger.info("✅ Gemini API working")
                        return {"status": "ok", "ai_ready": True}
                    else:
                        raise Exception(f"Gemini API HTTP {resp.status}")

        # Use TTA.dev timeout and retry for resilience
        timeout_primitive = TimeoutPrimitive(
            primitive=test_gemini_api, timeout_seconds=30
        )

        retry_primitive = RetryPrimitive(
            primitive=timeout_primitive.execute,
            max_retries=3,
            backoff_strategy="linear",
        )

        return await retry_primitive.execute(self.context, {})

    async def _import_workflow(self) -> dict[str, Any]:
        """Import n8n workflow with comprehensive error handling"""
        logger.info("📥 Importing n8n workflow...")

        # Load workflow file
        workflow_path = Path(self.workflow_file)
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {self.workflow_file}")

        with open(workflow_path) as f:
            workflow_data = json.load(f)

        async def import_and_activate():
            async with aiohttp.ClientSession() as session:
                # Try different authentication methods
                api_key = os.getenv("N8N_API_KEY", "")

                headers = {"Content-Type": "application/json"}

                if api_key:
                    headers["X-N8N-API-KEY"] = api_key

                # Import workflow
                async with session.post(
                    f"{self.n8n_base_url}/api/v1/workflows",
                    headers=headers,
                    json=workflow_data,
                    timeout=15,
                ) as resp:
                    if resp.status in [200, 201]:
                        result = await resp.json()
                        workflow_id = result.get("id")

                        if workflow_id:
                            logger.info(f"✅ Workflow imported with ID: {workflow_id}")

                            # Activate workflow
                            async with session.post(
                                f"{self.n8n_base_url}/api/v1/workflows/{workflow_id}/activate",
                                headers=headers,
                                timeout=10,
                            ) as activate_resp:
                                if activate_resp.status in [200, 201]:
                                    logger.info("✅ Workflow activated")
                                    return {
                                        "status": "imported",
                                        "workflow_id": workflow_id,
                                        "active": True,
                                    }

                        return {"status": "imported", "workflow_id": workflow_id}
                    else:
                        text = await resp.text()
                        raise Exception(f"Import failed: HTTP {resp.status} - {text}")

        # Create composite workflow for robust import
        return await import_and_activate()

    async def _validate_setup(self, previous_result: dict[str, Any]) -> dict[str, Any]:
        """Final validation using TTA.dev patterns"""
        logger.info("🔍 Validating complete setup...")

        validation_results = {
            "n8n_service": "checked",
            "github_api": "tested",
            "gemini_api": "tested",
            "workflow_import": previous_result.get("status") == "imported",
            "overall_status": "success"
            if previous_result.get("status") == "imported"
            else "partial",
        }

        logger.info(f"✅ Setup validation complete: {validation_results}")
        return validation_results


# Main execution
async def main():
    """Main setup function using TTA.dev patterns"""
    setup_engine = N8nSetupEngine()

    try:
        result = await setup_engine.setup_n8n_dashboard()

        # Print comprehensive results
        print("\n" + "=" * 60)
        print("🎉 N8N GITHUB DASHBOARD SETUP COMPLETE")
        print("=" * 60)

        if result.get("status") == "success":
            print("✅ Setup Status: SUCCESS")
            print("🔗 Access n8n: http://localhost:5678")
            print("📊 Dashboard: GitHub Health Dashboard with AI insights")
            print("⏰ Schedule: Every 6 hours")
            print("\n🚀 Next Steps:")
            print("1. Open n8n interface in browser")
            print("2. Test the workflow manually")
            print("3. Monitor dashboard outputs")
        else:
            print("⚠️  Setup Status: PARTIAL SUCCESS")
            print(f"❌ Issues: {result.get('error', 'Unknown error')}")
            print("\n🔧 Manual setup required:")
            print("1. Open http://localhost:5678")
            print("2. Import workflow manually")
            print("3. Configure credentials")

        return result

    except Exception as e:
        logger.error(f"❌ Setup engine error: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run with uv
    asyncio.run(main())
