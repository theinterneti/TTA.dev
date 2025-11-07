"""LLM Integration for ACE Self-Learning Code Generation.

This module provides real LLM-powered code generation using Google AI Studio's
Gemini 2.5 Pro model (free tier).

Phase 2 Implementation:
- Replaces mock template-based code generation
- Uses Gemini 2.5 Pro for production-quality code
- Implements strategy-aware prompting
- Handles rate limits and API errors gracefully
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Try to import Google AI SDK (optional dependency for Phase 2)
try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning(
        "google-generativeai not installed. Install with: uv add google-generativeai"
    )


class LLMCodeGenerator:
    """LLM-powered code generator using Google AI Studio (Gemini 2.5 Pro).

    Features:
    - Zero-cost code generation (free tier)
    - Strategy-aware prompting (injects learned strategies)
    - Error handling for rate limits
    - Fallback to mock implementation if API unavailable

    Example:
        ```python
        generator = LLMCodeGenerator()
        code = await generator.generate_code(
            task="Create pytest tests for CachePrimitive",
            context="Test cache hit/miss scenarios",
            language="python",
            strategies=["use pytest-asyncio", "mock the wrapped primitive"]
        )
        ```
    """

    def __init__(
        self, api_key: str | None = None, model_name: str = "gemini-2.0-flash-exp"
    ):
        """Initialize LLM code generator.

        Args:
            api_key: Google AI Studio API key (defaults to GEMINI_API_KEY or GOOGLE_AI_STUDIO_API_KEY env var)
            model_name: Gemini model to use (default: gemini-2.0-flash-exp for best balance)
        """
        # Check multiple environment variable names
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_AI_STUDIO_API_KEY")
        )
        self.model_name = model_name
        self.model = None

        if GENAI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"LLM code generator initialized with {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            if not GENAI_AVAILABLE:
                logger.warning(
                    "Google AI SDK not available - using mock implementation"
                )
            elif not self.api_key:
                logger.warning(
                    "GOOGLE_AI_STUDIO_API_KEY not set - using mock implementation"
                )

    async def generate_code(
        self,
        task: str,
        context: str,
        language: str,
        strategies: list[str],
        source_code: str | None = None,
    ) -> str:
        """Generate code using LLM + learned strategies.

        Args:
            task: Code generation task description
            context: Additional context about the task
            language: Programming language (e.g., "python")
            strategies: List of learned strategies to apply
            source_code: Optional source code to reference (prevents API hallucination)

        Returns:
            Generated code as string
        """
        if self.model is None:
            # Fallback to mock implementation
            return await self._mock_generate_code(task, context, language, strategies)

        try:
            # Build strategy-aware prompt (with optional source code)
            prompt = self._build_prompt(
                task, context, language, strategies, source_code
            )

            # Generate code using Gemini
            response = await self.model.generate_content_async(prompt)

            # Extract code from response
            code = self._extract_code(response.text)

            logger.info(f"Generated {len(code)} characters of {language} code")
            return code

        except Exception as e:
            logger.error(f"LLM code generation failed: {e}")
            # Fallback to mock on error
            return await self._mock_generate_code(task, context, language, strategies)

    def _build_prompt(
        self,
        task: str,
        context: str,
        language: str,
        strategies: list[str],
        source_code: str | None = None,
    ) -> str:
        """Build strategy-aware prompt for LLM.

        Args:
            task: Code generation task
            context: Additional context
            language: Programming language
            strategies: Learned strategies to apply
            source_code: Optional source code to reference (prevents API hallucination)

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert {language} developer. Generate production-quality code for the following task.

**Task:** {task}

**Context:** {context}

**Language:** {language}

"""

        # Add source code reference if provided (Phase 3 enhancement)
        if source_code:
            prompt += f"""**Reference Source Code:**
Use this source code as a reference for the correct API and usage patterns.
DO NOT hallucinate APIs - use only what's shown in this reference code.

```{language}
{source_code}
```

"""

        if strategies:
            prompt += "**Apply these learned strategies:**\n"
            for i, strategy in enumerate(strategies, 1):
                prompt += f"{i}. {strategy}\n"
            prompt += "\n"

        prompt += """**Requirements:**
- Generate complete, working code
- Include proper imports and dependencies
- Add error handling where appropriate
- Include docstrings and comments
- Follow best practices and conventions
- Make the code production-ready
- If reference source code is provided, use its exact API (method names, parameters, etc.)

**Output Format:**
- Return ONLY the code, no explanations
- Use proper indentation and formatting
- Include any necessary test code or examples

Generate the code now:
"""

        return prompt

    def _extract_code(self, response_text: str) -> str:
        """Extract code from LLM response.

        Args:
            response_text: Raw LLM response

        Returns:
            Extracted code (removes markdown code blocks if present)
        """
        # Remove markdown code blocks if present
        if "```" in response_text:
            # Extract code between ``` markers
            parts = response_text.split("```")
            if len(parts) >= 3:
                # Get the code block (skip language identifier if present)
                code_block = parts[1]
                if "\n" in code_block:
                    lines = code_block.split("\n")
                    # Skip first line if it's a language identifier
                    if lines[0].strip() in [
                        "python",
                        "py",
                        "javascript",
                        "js",
                        "typescript",
                        "ts",
                    ]:
                        return "\n".join(lines[1:])
                return code_block
        return response_text

    async def _mock_generate_code(
        self, task: str, context: str, language: str, strategies: list[str]
    ) -> str:
        """Fallback mock implementation (same as original).

        Used when LLM is unavailable or fails.
        """
        # Simple template-based generation (original mock implementation)
        return f"""try:
# Generated code for: {task}
print("Hello from generated code!")
print("Task: {task}")
print("Context: {context}")
print("Language: {language}")
except Exception as e:
    print(f"Error occurred: {{e}}")
    print("Implementing error handling based on learned strategies")
"""
