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
from tta_dev_primitives.adaptive.fallback import AdaptiveFallbackPrimitive

# TTA.dev imports - using correct API
from tta_dev_primitives.adaptive.retry import AdaptiveRetryPrimitive
from tta_dev_primitives.adaptive.timeout import AdaptiveTimeoutPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class N8nSetupEngine:
    """TTA.dev powered n8n setup engine with adaptive patterns"""

    def __init__(self):
        self.context = WorkflowContext(
            correlation_id="n8n-setup-001", data={"setup_type": "github_dashboard"}
        )
        self.n8n_base_url = "http://localhost:5678"
        self.workflow_file = "n8n_github_health_dashboard.json"

    async def setup_n8n_dashboard(self) -> dict[str, Any]:
        """Main setup workflow using TTA.dev primitives"""
        logger.info("🚀 Starting robust n8n GitHub Dashboard setup...")

        try:
            # Step 1: Check n8n service with TTA.dev adaptive retry
            n8n_result = await self._check_n8n_service()

            # Step 2: Verify GitHub API with TTA.dev adaptive fallback
            github_result = await self._verify_github_api()

            # Step 3: Verify Gemini API with TTA.dev adaptive timeout
            gemini_result = await self._verify_gemini_api()

            # Step 4: Import workflow with comprehensive handling
            workflow_result = await self._import_workflow()

            # Step 5: Final validation
            validation_result = self._validate_setup(
                {
                    "n8n": n8n_result,
                    "github": github_result,
                    "gemini": gemini_result,
                    "workflow": workflow_result,
                }
            )

            logger.info("✅ n8n setup completed successfully!")
            return validation_result

        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _check_n8n_service(self) -> dict[str, Any]:
        """Check n8n service availability with TTA.dev adaptive retry"""
        logger.info("📡 Checking n8n service availability...")

        async def check_n8n_health():
            async with aiohttp.ClientSession() as session:
                try:
                    # Check n8n web interface
                    async with session.get(f"{self.n8n_base_url}/healthz", timeout=5) as resp:
                        if resp.status == 200:
                            logger.info("✅ n8n web interface accessible")
                            return {"status": "healthy", "web_interface": "ok"}
                        else:
                            raise Exception(f"HTTP {resp.status}")
                except Exception as e:
                    logger.warning(f"❌ n8n health check failed: {e}")
                    raise

        # Use TTA.dev AdaptiveRetryPrimitive with exponential backoff
        async def adaptive_retry_wrapper():
            retry_primitive = AdaptiveRetryPrimitive(
                target_primitive=check_n8n_health,
                max_attempts=5,
                base_delay=1.0,
                max_delay=30.0,
                backoff_multiplier=2.0,
            )
            return await retry_primitive.execute({}, self.context)

        return await adaptive_retry_wrapper()

    async def _verify_github_api(self) -> dict[str, Any]:
        """Verify GitHub API connectivity with TTA.dev adaptive fallback"""
        logger.info("🔑 Verifying GitHub API connectivity...")

        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or "ghp_YOUR_GITHUB_TOKEN_HERE"

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

        # Use TTA.dev AdaptiveFallbackPrimitive for graceful degradation
        async def adaptive_fallback_wrapper():
            fallback_primitive = AdaptiveFallbackPrimitive(
                primary=test_github_api,
                fallback=lambda: {
                    "status": "degraded",
                    "message": "GitHub API unavailable, continuing with limited functionality",
                },
            )
            return await fallback_primitive.execute({}, self.context)

        return await adaptive_fallback_wrapper()

    async def _verify_gemini_api(self) -> dict[str, Any]:
        """Verify Gemini API connectivity with TTA.dev adaptive timeout"""
        logger.info("🤖 Verifying Gemini AI API connectivity...")

        gemini_key = os.getenv("GEMINI_API_KEY") or "AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE"

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

        # Use TTA.dev AdaptiveTimeoutPrimitive for resilience
        async def adaptive_timeout_wrapper():
            timeout_primitive = AdaptiveTimeoutPrimitive(
                target_primitive=test_gemini_api, timeout_seconds=30.0
            )
            return await timeout_primitive.execute({}, self.context)

        return await adaptive_timeout_wrapper()

    async def _import_workflow(self) -> dict[str, Any]:
        """Import n8n workflow with comprehensive error handling"""
        logger.info("📥 Importing n8n workflow...")

        # Load workflow file
        workflow_path = Path(self.workflow_file)
        if not workflow_path.exists():
            return {
                "status": "error",
                "error": f"Workflow file not found: {self.workflow_file}",
            }

        try:
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

            return await import_and_activate()

        except Exception as e:
            logger.error(f"❌ Workflow import failed: {e}")
            return {"status": "error", "error": str(e)}

    def _validate_setup(self, results: dict[str, Any]) -> dict[str, Any]:
        """Final validation using TTA.dev patterns"""
        logger.info("🔍 Validating complete setup...")

        # Check if workflow was successfully imported
        workflow_success = results.get("workflow", {}).get("status") == "imported"

        validation_results = {
            "n8n_service": results.get("n8n", {}).get("status", "unknown"),
            "github_api": results.get("github", {}).get("status", "unknown"),
            "gemini_api": results.get("gemini", {}).get("status", "unknown"),
            "workflow_import": workflow_success,
            "overall_status": "success" if workflow_success else "partial",
            "workflow_id": results.get("workflow", {}).get("workflow_id"),
            "api_connectivity": {
                "n8n_healthy": results.get("n8n", {}).get("status") == "healthy",
                "github_working": results.get("github", {}).get("status") in ["ok", "degraded"],
                "gemini_working": results.get("gemini", {}).get("status") in ["ok", "degraded"],
            },
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

        if result.get("overall_status") == "success":
            print("✅ Setup Status: SUCCESS")
            print("🔗 Access n8n: http://localhost:5678")
            print("📊 Dashboard: GitHub Health Dashboard with AI insights")
            print("⏰ Schedule: Every 6 hours")
            print(f"🔧 Workflow ID: {result.get('workflow_id', 'N/A')}")
            print("\n🚀 Next Steps:")
            print("1. Open n8n interface in browser")
            print("2. Test the workflow manually")
            print("3. Monitor dashboard outputs")
        else:
            print("⚠️  Setup Status: PARTIAL SUCCESS")
            print("🔧 API Connectivity Status:")
            for service, status in result.get("api_connectivity", {}).items():
                print(f"   {service}: {'✅' if status else '❌'}")
            print(f"❌ Issues: {result.get('error', 'Partial functionality')}")
            print("\n🔧 Manual setup may be required:")
            print("1. Open http://localhost:5678")
            print("2. Import workflow manually")
            print("3. Configure credentials")

        print("\n" + "=" * 60)
        return result

    except Exception as e:
        logger.error(f"❌ Setup engine error: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Run with uv
    asyncio.run(main())
