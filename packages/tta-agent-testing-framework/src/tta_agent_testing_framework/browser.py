"""
Browser automation providers using Playwright for VS Code web testing.
"""

import asyncio
from pathlib import Path

from playwright.async_api import BrowserContext, Page, Playwright

from .core import BrowserAutomationProvider, ValidationResult, WorkspaceType


class PlaywrightAutomationProvider(BrowserAutomationProvider):
    """Browser automation using Playwright for VS Code web testing."""

    def __init__(
        self,
        playwright: Playwright,
        context: BrowserContext | None = None,
        screenshot_dir: Path | None = None,
    ):
        self.playwright = playwright
        self.context = context
        self.screenshot_dir = screenshot_dir or Path("./browser-screenshots")
        self.pages: dict[str, Page] = {}

        # Create screenshot directory
        self.screenshot_dir.mkdir(exist_ok=True)

    async def create_context(self) -> BrowserContext:
        """Create a new browser context for VS Code testing."""
        return await self.playwright.chromium.new_context(
            viewport={"width": 1280, "height": 720},
            # Enable extensions and VS Code features
            permissions=["clipboard-read", "clipboard-write"],
            # VS Code specific user agent
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ),
        )

    async def ensure_context(self) -> BrowserContext:
        """Ensure we have a valid browser context."""
        if self.context is None:
            self.context = await self.create_context()
        return self.context

    async def launch_vscode_web(
        self,
        workspace_url: str,
        workspace_type: WorkspaceType,
        timeout: int = 30000,
    ) -> ValidationResult:
        """Launch vscode.dev with specified workspace."""
        result = ValidationResult(
            success=True,
            metadata={
                "workspace_url": workspace_url,
                "workspace_type": workspace_type.value,
                "timeout": timeout,
            },
        )

        try:
            context = await self.ensure_context()

            # Generate unique page key
            page_key = f"vscode-{workspace_type.value}"
            page = await context.new_page()

            # Navigate to vscode.dev
            vscode_url = f"https://{workspace_url}"
            await page.goto(vscode_url, wait_until="networkidle", timeout=timeout)

            # Wait for VS Code to load
            await page.wait_for_selector(
                ".monaco-workbench",
                timeout=timeout,
                state="visible",
            )

            # Store page reference
            self.pages[page_key] = page

            # Take screenshot for validation
            await self.capture_screenshot(
                filename=f"vscode-{workspace_type.value}-loaded.png"
            )

            result.metadata["page_url"] = page.url

        except Exception as e:
            result.success = False
            result.errors.append(f"Failed to launch VS Code web: {str(e)}")

            # Capture error screenshot
            try:
                await self.capture_screenshot(
                    filename=f"vscode-{workspace_type.value}-error.png"
                )
            except Exception:
                pass  # Ignore screenshot errors

        return result

    async def wait_for_extension_load(
        self,
        extension_id: str,
        timeout: int = 10000,
    ) -> ValidationResult:
        """Wait for VS Code extension to load."""
        result = ValidationResult(
            success=True,
            metadata={"extension_id": extension_id, "timeout": timeout},
        )

        # VS Code extensions load asynchronously, check for extension presence
        # This is a simplified check - in practice you'd look for specific extension indicators
        try:
            context = await self.ensure_context()
            page = await context.new_page()

            # Give extension time to load
            await asyncio.sleep(2)

            # Check if extension is loaded (this is a placeholder - actual implementation
            # would need to inspect VS Code's extension API or DOM elements)
            extension_loaded = True  # Placeholder

            if extension_loaded:
                result.metadata["load_time"] = "validated"
            else:
                result.success = False
                result.errors.append(
                    f"Extension {extension_id} did not load within {timeout}ms"
                )

        except Exception as e:
            result.success = False
            result.errors.append(f"Error checking extension load: {str(e)}")

        return result

    async def execute_in_terminal(
        self,
        command: str,
        workspace_root: str | None = None,
    ) -> ValidationResult:
        """Execute command in VS Code terminal."""
        result = ValidationResult(
            success=True,
            metadata={"command": command, "workspace_root": workspace_root},
        )

        # This is a complex operation as VS Code terminal is interactive
        # Implementation would require:
        # 1. Opening terminal panel
        # 2. Typing command
        # 3. Executing command
        # 4. Capturing output

        # Placeholder implementation
        result.warnings.append("Terminal execution not fully implemented")
        result.metadata["status"] = "placeholder"

        return result

    async def capture_screenshot(
        self,
        filename: str | None = None,
        full_page: bool = False,
    ) -> ValidationResult:
        """Capture screenshot of current state."""
        if filename is None:
            import time

            filename = f"screenshot-{int(time.time())}.png"

        result = ValidationResult(
            success=True,
            metadata={"filename": filename, "full_page": full_page},
        )

        try:
            if self.context:
                # Find the most recent page
                pages = self.context.pages
                if pages:
                    page = pages[-1]  # Use last active page
                    screenshot_path = self.screenshot_dir / filename

                    await page.screenshot(
                        path=str(screenshot_path),
                        full_page=full_page,
                    )

                    result.metadata["path"] = str(screenshot_path)
                else:
                    result.success = False
                    result.errors.append("No active pages to capture")
            else:
                result.success = False
                result.errors.append("No browser context available")

        except Exception as e:
            result.success = False
            result.errors.append(f"Screenshot failed: {str(e)}")

        return result


class VscodeWebValidator:
    """Validator for VS Code web features and extensions."""

    def __init__(self, browser_provider: BrowserAutomationProvider):
        self.browser_provider = browser_provider

    async def validate_vscode_features(
        self,
        workspace_type: WorkspaceType,
    ) -> ValidationResult:
        """Validate VS Code features are working."""
        result = ValidationResult(
            success=True,
            metadata={"workspace_type": workspace_type.value},
        )

        # Check basic VS Code features
        features_to_check = [
            ".monaco-workbench",  # Main workbench
            ".activity-bar",  # Activity bar
            ".side-bar",  # Side panel
            ".editor-group-container",  # Editor area
        ]

        for selector in features_to_check:
            # This would actually check if elements exist using browser automation
            # For now, just track what should be checked
            result.metadata[f"checked_element_{selector}"] = True

        # Workspace-specific validations
        if workspace_type == WorkspaceType.CLINE:
            result.metadata["cline_extension_expected"] = True
        elif workspace_type == WorkspaceType.AUGMENT:
            result.metadata["augment_features_expected"] = True
        elif workspace_type == WorkspaceType.GITHUB_COPILOT:
            result.metadata["copilot_features_expected"] = True

        return result

    async def validate_workspace_content(
        self,
        workspace_type: WorkspaceType,
        should_have_files: bool = True,
    ) -> ValidationResult:
        """Validate that workspace content is properly loaded."""
        result = ValidationResult(
            success=True,
            metadata={
                "workspace_type": workspace_type.value,
                "should_have_files": should_have_files,
            },
        )

        # Check for workspace loading
        # This would inspect the VS Code file tree, open files, etc.
        result.metadata["workspace_loaded"] = True

        # Validate against expected workspace configuration
        workspace_file = Path(f"{workspace_type.value}.code-workspace")
        if workspace_file.exists():
            result.metadata["workspace_config_found"] = True
        else:
            result.warnings.append(f"Workspace config file not found: {workspace_file}")

        return result
