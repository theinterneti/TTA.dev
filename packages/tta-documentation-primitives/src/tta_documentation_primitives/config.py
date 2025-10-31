"""Configuration management for tta-documentation-primitives.

Loads and validates configuration from .tta-docs.json file.
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    """AI provider configuration."""

    provider: str = Field(
        default="gemini", description="AI provider (gemini, ollama, none)"
    )
    model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Model name for the provider",
    )
    fallback: str | None = Field(
        default="ollama:llama3.2:3b",
        description="Fallback model if primary fails",
    )
    api_key: str | None = Field(default=None, description="API key for provider")


class SyncConfig(BaseModel):
    """Synchronization configuration."""

    auto: bool = Field(
        default=True, description="Enable automatic sync on file changes"
    )
    debounce_ms: int = Field(default=500, description="Debounce delay in milliseconds")
    bidirectional: bool = Field(
        default=True,
        description="Enable Logseq → docs sync (with sync-to-docs property)",
    )


class FormatConfig(BaseModel):
    """Format configuration."""

    dual_format: bool = Field(
        default=True, description="Generate AI-optimized metadata section"
    )
    preserve_code_blocks: bool = Field(
        default=True, description="Preserve code block formatting"
    )
    convert_links: bool = Field(
        default=True, description="Convert markdown links to [[Logseq]]"
    )


class TTADocsConfig(BaseModel):
    """Main configuration for tta-documentation-primitives."""

    docs_paths: list[str] = Field(
        default=["docs/", "packages/*/README.md"],
        description="Paths to monitor for documentation changes",
    )
    logseq_path: str = Field(
        default="logseq/pages/", description="Path to Logseq pages directory"
    )
    ai: AIConfig = Field(default_factory=AIConfig, description="AI configuration")
    sync: SyncConfig = Field(
        default_factory=SyncConfig, description="Sync configuration"
    )
    format: FormatConfig = Field(
        default_factory=FormatConfig, description="Format configuration"
    )

    @classmethod
    def load(cls, config_path: Path | None = None) -> "TTADocsConfig":
        """Load configuration from file or use defaults.

        Args:
            config_path: Path to .tta-docs.json file. If None, searches for file in
                current directory and parent directories.

        Returns:
            Loaded configuration with defaults for missing values.
        """
        if config_path is None:
            config_path = cls._find_config_file()

        if config_path and config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
            return cls(**data)

        return cls()

    @staticmethod
    def _find_config_file() -> Path | None:
        """Search for .tta-docs.json in current and parent directories.

        Returns:
            Path to config file if found, None otherwise.
        """
        current = Path.cwd()
        for _ in range(10):  # Search up to 10 parent directories
            config_path = current / ".tta-docs.json"
            if config_path.exists():
                return config_path
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent
        return None

    def save(self, config_path: Path) -> None:
        """Save configuration to file.

        Args:
            config_path: Path where to save the configuration.
        """
        with open(config_path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)


def get_default_config() -> TTADocsConfig:
    """Get default configuration.

    Returns:
        Default TTADocsConfig instance.
    """
    return TTADocsConfig()


def load_config(config_path: Path | None = None) -> TTADocsConfig:
    """Load configuration from file or return defaults.

    Args:
        config_path: Optional path to config file.

    Returns:
        Loaded or default configuration.
    """
    return TTADocsConfig.load(config_path)
