"""
Langfuse Prompt Management

This module provides utilities for managing prompts in Langfuse via the API.
Supports creating, updating, fetching, and versioning prompts.
"""

from typing import Any

from langfuse import Langfuse

from .initialization import get_langfuse_client, is_langfuse_enabled


class PromptManager:
    """Manage prompts in Langfuse."""

    def __init__(self, client: Langfuse | None = None):
        """
        Initialize prompt manager.

        Args:
            client: Langfuse client instance. If None, will get from initialization module.
        """
        self.client = client or get_langfuse_client()

    def create_prompt(
        self,
        name: str,
        prompt: str,
        config: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new prompt in Langfuse.

        Args:
            name: Unique name for the prompt
            prompt: The prompt text/template
            config: Optional configuration (model, temperature, etc.)
            labels: Optional labels for categorization
            tags: Optional tags for filtering

        Returns:
            Dict containing prompt details including name, version, and content

        Example:
            >>> manager = PromptManager()
            >>> result = manager.create_prompt(
            ...     name="code-review-prompt",
            ...     prompt="Review this code: {{code}}",
            ...     config={"model": "gpt-4", "temperature": 0.3},
            ...     labels=["code-quality"],
            ...     tags=["production", "review"]
            ... )
        """
        if not is_langfuse_enabled():
            return {
                "name": name,
                "version": 0,
                "prompt": prompt,
                "config": config or {},
                "disabled": True,
            }

        try:
            # Langfuse prompt creation
            created = self.client.create_prompt(
                name=name,
                prompt=prompt,
                config=config or {},
                labels=labels or [],
                tags=tags or [],
            )

            return {
                "name": created.name,
                "version": created.version,
                "prompt": created.prompt,
                "config": created.config,
                "labels": getattr(created, "labels", []),
                "tags": getattr(created, "tags", []),
            }
        except Exception as e:
            raise RuntimeError(f"Failed to create prompt '{name}': {e}") from e

    def get_prompt(
        self,
        name: str,
        version: int | None = None,
        label: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Fetch a prompt from Langfuse.

        Args:
            name: Name of the prompt
            version: Specific version to fetch (None = latest)
            label: Label to filter by (e.g., "production")

        Returns:
            Dict with prompt details or None if not found

        Example:
            >>> manager = PromptManager()
            >>> prompt = manager.get_prompt("code-review-prompt", version=2)
            >>> compiled = prompt["prompt"].format(code="def foo(): pass")
        """
        if not is_langfuse_enabled():
            return None

        try:
            if label:
                fetched = self.client.get_prompt(name=name, label=label)
            elif version is not None:
                fetched = self.client.get_prompt(name=name, version=version)
            else:
                fetched = self.client.get_prompt(name=name)

            if not fetched:
                return None

            return {
                "name": fetched.name,
                "version": fetched.version,
                "prompt": fetched.prompt,
                "config": fetched.config,
                "labels": getattr(fetched, "labels", []),
                "tags": getattr(fetched, "tags", []),
            }
        except Exception as e:
            print(f"Warning: Failed to fetch prompt '{name}': {e}")
            return None

    def compile_prompt(
        self,
        name: str,
        variables: dict[str, Any],
        version: int | None = None,
        label: str | None = None,
    ) -> str | None:
        """
        Fetch and compile a prompt with variables.

        Args:
            name: Name of the prompt
            variables: Variables to inject into the prompt template
            version: Specific version to use
            label: Label to filter by

        Returns:
            Compiled prompt string or None if not found

        Example:
            >>> manager = PromptManager()
            >>> compiled = manager.compile_prompt(
            ...     name="code-review-prompt",
            ...     variables={"code": "def foo(): pass"}
            ... )
        """
        prompt_data = self.get_prompt(name=name, version=version, label=label)

        if not prompt_data:
            return None

        try:
            # Simple string replacement for {{variable}} syntax
            compiled = prompt_data["prompt"]
            for key, value in variables.items():
                compiled = compiled.replace(f"{{{{{key}}}}}", str(value))

            return compiled
        except Exception as e:
            print(f"Warning: Failed to compile prompt '{name}': {e}")
            return None

    def update_prompt(
        self,
        name: str,
        prompt: str | None = None,
        config: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Update an existing prompt (creates a new version).

        Args:
            name: Name of the prompt to update
            prompt: New prompt text (None = keep existing)
            config: New config (None = keep existing)
            labels: New labels (None = keep existing)
            tags: New tags (None = keep existing)

        Returns:
            Dict with new prompt version details

        Example:
            >>> manager = PromptManager()
            >>> updated = manager.update_prompt(
            ...     name="code-review-prompt",
            ...     config={"temperature": 0.5}  # Update just temperature
            ... )
        """
        if not is_langfuse_enabled():
            return {
                "name": name,
                "version": 0,
                "disabled": True,
            }

        # Fetch current prompt to get existing values
        current = self.get_prompt(name=name)
        if not current:
            raise ValueError(f"Prompt '{name}' not found")

        # Merge with new values
        final_prompt = prompt if prompt is not None else current["prompt"]
        final_config = config if config is not None else current["config"]
        final_labels = labels if labels is not None else current.get("labels", [])
        final_tags = tags if tags is not None else current.get("tags", [])

        # Create new version
        return self.create_prompt(
            name=name,
            prompt=final_prompt,
            config=final_config,
            labels=final_labels,
            tags=final_tags,
        )

    def list_prompts(self) -> list[dict[str, Any]]:
        """
        List all available prompts (not directly supported by SDK).

        Note: The Langfuse Python SDK doesn't have a list_prompts method.
        This would require using the REST API directly.

        Returns:
            Empty list (placeholder for future implementation)
        """
        # TODO: Implement using REST API if needed
        return []


def create_prompt_from_instruction_file(
    instruction_file_path: str,
    name: str,
    apply_to_pattern: str,
    description: str,
    labels: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a Langfuse prompt from a .instructions.md file.

    Args:
        instruction_file_path: Path to the .instructions.md file
        name: Unique name for the prompt
        apply_to_pattern: File pattern this applies to (from frontmatter)
        description: Description of the prompt's purpose
        labels: Optional labels
        tags: Optional tags

    Returns:
        Dict with created prompt details

    Example:
        >>> result = create_prompt_from_instruction_file(
        ...     instruction_file_path=".github/instructions/testing.instructions.md",
        ...     name="testing-standards",
        ...     apply_to_pattern="**/tests/**/*.py",
        ...     description="Testing standards and best practices",
        ...     labels=["code-quality"],
        ...     tags=["testing", "standards"]
        ... )
    """
    import pathlib

    file_path = pathlib.Path(instruction_file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Instruction file not found: {instruction_file_path}")

    # Read the file content
    content = file_path.read_text()

    # Remove YAML frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    # Create prompt with metadata
    manager = PromptManager()

    config = {
        "apply_to": apply_to_pattern,
        "description": description,
        "source_file": str(file_path),
    }

    return manager.create_prompt(
        name=name,
        prompt=content,
        config=config,
        labels=labels or ["instruction"],
        tags=tags or [],
    )
