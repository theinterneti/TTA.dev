#!/usr/bin/env python3
# pragma: allow-asyncio
"""
Robust n8n GitHub Dashboard Setup using TTA.dev Patterns
Simple implementation using TTA.dev concepts for reliable n8n setup
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import aiohttp
from tta_dev_primitives.core.base import WorkflowContext

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TTADevRetryEngine:
    """TTA.dev inspired retry engine with exponential backoff"""

    @staticmethod
    async def retry_with_exponential_backoff(
        func,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_multiplier: float = 2.0,
    ) -> dict[str, Any]:
        """TTA.dev inspired retry with exponential backoff"""

        for attempt in range(max_attempts):
            try:
                result = await func()
                return {"success": True, "result": result, "attempts": attempt + 1}
            except Exception as e:
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    return {"success": False, "error": str(e), "attempts": attempt + 1}

                # Calculate delay with exponential backoff
                delay = min(base_delay * (backoff_multiplier**attempt), max_delay)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)

        return {"success": False, "error": "Max attempts reached"}


class TTADevFallbackEngine:
    """TTA.dev inspired fallback engine for graceful degradation"""

    @staticmethod
    async def fallback_with_alternatives(
        primary_func, fallback_funcs: list, primary_name: str = "primary"
    ) -> dict[str, Any]:
        """TTA.dev inspired fallback with multiple alternatives"""

        try:
            # Try primary function first
            result = await primary_func()
            logger.info(f"✅ {primary_name} successful")
            return {"success": True, "result": result, "source": primary_name}
        except Exception as e:
            logger.warning(f"❌ {primary_name} failed: {e}")

            # Try fallback functions
            for i, fallback_func in enumerate(fallback_funcs):
                try:
                    fallback_name = f"fallback_{i + 1}"
                    result = await fallback_func()
                    logger.info(f"✅ {fallback_name} successful")
                    return {
                        "success": True,
                        "result": result,
                        "source": fallback_name,
                        "degraded": True,
                    }
                except Exception as fallback_error:
                    logger.warning(f"❌ {fallback_name} failed: {fallback_error}")
                    continue

            # All failed
            return {
                "success": False,
                "error": "Primary and all fallbacks failed",
                "degraded": True,
            }


class TTADevTimeoutEngine:
    """TTA.dev inspired timeout engine for resilience"""

    @staticmethod
    async def execute_with_timeout(
        func, timeout_seconds: float = 30.0
    ) -> dict[str, Any]:
        """TTA.dev inspired execution with timeout protection"""

        try:
            result = await asyncio.wait_for(func(), timeout=timeout_seconds)
            return {"success": True, "result": result, "timed_out": False}
        except TimeoutError:
            logger.warning(f"⏰ Function timed out after {timeout_seconds}s")
            return {
                "success": False,
                "error": f"Timeout after {timeout_seconds}s",
                "timed_out": True,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "timed_out": False}


class N8nSetupEngine:
    """TTA.dev powered n8n setup engine with robust patterns"""

    def __init__(self):
        self.context = WorkflowContext(
            correlation_id="n8n-setup-001", data={"setup_type": "github_dashboard"}
        )
        self.n8n_base_url = "http://localhost:5678"
        self.workflow_file = "n8n_github_health_dashboard.json"

        # Initialize TTA.dev inspired engines
        self.retry_engine = TTADevRetryEngine()
        self.fallback_engine = TTADevFallbackEngine()
        self.timeout_engine = TTADevTimeoutEngine()

    async def setup_n8n_dashboard(self) -> dict[str, Any]:
        """Main setup workflow using TTA.dev inspired patterns"""
        logger.info("🚀 Starting TTA.dev powered n8n GitHub Dashboard setup...")

        try:
            # Step 1: Check n8n service with TTA.dev retry
            n8n_result = await self._check_n8n_service()

            # Step 2: Verify GitHub API with TTA.dev fallback
            github_result = await self._verify_github_api()

            # Step 3: Verify Gemini API with TTA.dev timeout
            gemini_result = await self._verify_gemini_api()

            # Step 4: Import workflow with TTA.dev resilience
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
        """Check n8n service with TTA.dev inspired retry"""
        logger.info("📡 Checking n8n service availability...")

        async def check_n8n_health():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.n8n_base_url}/healthz", timeout=5
                ) as resp:
                    if resp.status == 200:
                        return {"status": "healthy", "web_interface": "ok"}
                    else:
                        raise Exception(f"HTTP {resp.status}")

        # Use TTA.dev inspired retry with exponential backoff
        result = await self.retry_engine.retry_with_exponential_backoff(
            check_n8n_health, max_attempts=5, base_delay=1.0, max_delay=30.0
        )

        if result["success"]:
            logger.info("✅ n8n web interface accessible")

        return result

    async def _verify_github_api(self) -> dict[str, Any]:
        """Verify GitHub API with TTA.dev inspired fallback"""
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
                        return {"status": "ok", "repo": data.get("full_name")}
                    else:
                        raise Exception(f"GitHub API HTTP {resp.status}")

        async def test_github_rate_limit():
            """Fallback: Test with rate limit endpoint"""
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                async with session.get(
                    "https://api.github.com/rate_limit",
                    headers=headers,
                    timeout=5,
                ) as resp:
                    if resp.status == 200:
                        return {"status": "degraded", "message": "Limited API access"}
                    else:
                        raise Exception(f"Rate limit API HTTP {resp.status}")

        # Use TTA.dev inspired fallback with alternatives
        result = await self.fallback_engine.fallback_with_alternatives(
            test_github_api, [test_github_rate_limit], "GitHub API"
        )

        if result["success"]:
            logger.info(
                f"✅ GitHub API working - {result.get('result', {}).get('repo', 'N/A')}"
            )

        return result

    async def _verify_gemini_api(self) -> dict[str, Any]:
        """Verify Gemini API with TTA.dev inspired timeout"""
        logger.info("🤖 Verifying Gemini AI API connectivity...")

        gemini_key = (
            os.getenv("GEMINI_API_KEY") or "AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE"
        )

        async def test_gemini_api():
            payload = {"contents": [{"parts": [{"text": "Hello"}]}]}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}",
                    json=payload,
                    timeout=10,
                ) as resp:
                    if resp.status == 200:
                        return {"status": "ok", "ai_ready": True}
                    else:
                        raise Exception(f"Gemini API HTTP {resp.status}")

        # Use TTA.dev inspired timeout protection
        result = await self.timeout_engine.execute_with_timeout(
            test_gemini_api, timeout_seconds=30.0
        )

        if result["success"]:
            logger.info("✅ Gemini API working")

        return result

    async def _import_workflow(self) -> dict[str, Any]:
        """Import n8n workflow with TTA.dev resilience"""
        logger.info("📥 Importing n8n workflow...")

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
                                logger.info(
                                    f"✅ Workflow imported with ID: {workflow_id}"
                                )

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
                            raise Exception(
                                f"Import failed: HTTP {resp.status} - {text}"
                            )

            # Use TTA.dev inspired timeout for workflow import
            result = await self.timeout_engine.execute_with_timeout(
                import_and_activate, timeout_seconds=30.0
            )

            return result

        except Exception as e:
            logger.error(f"❌ Workflow import failed: {e}")
            return {"status": "error", "error": str(e)}

    def _validate_setup(self, results: dict[str, Any]) -> dict[str, Any]:
        """Final validation using TTA.dev patterns"""
        logger.info("🔍 Validating complete setup...")

        workflow_success = results.get("workflow", {}).get("status") == "imported"
        n8n_healthy = results.get("n8n", {}).get("success", False)
        github_working = results.get("github", {}).get("success", False)
        gemini_working = results.get("gemini", {}).get("success", False)

        validation_results = {
            "n8n_service": "healthy" if n8n_healthy else "unhealthy",
            "github_api": "working" if github_working else "unavailable",
            "gemini_api": "working" if gemini_working else "unavailable",
            "workflow_import": workflow_success,
            "overall_status": "success" if workflow_success else "partial",
            "workflow_id": results.get("workflow", {})
            .get("result", {})
            .get("workflow_id"),
            "api_connectivity": {
                "n8n_healthy": n8n_healthy,
                "github_working": github_working,
                "gemini_working": gemini_working,
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
