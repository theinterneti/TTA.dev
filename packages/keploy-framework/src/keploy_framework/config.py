"""Configuration management for Keploy."""

import yaml
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration."""

    command: str = Field(description="Command to start the application")
    port: int = Field(default=8000, description="Application port")
    host: str = Field(default="0.0.0.0", description="Application host")


class TestConfig(BaseModel):
    """Test configuration."""

    path: str = Field(default="./keploy/tests", description="Path to test directory")
    global_noise: dict[str, Any] = Field(
        default_factory=dict, alias="globalNoise", description="Global noise filters"
    )


class KeployConfig(BaseModel):
    """Keploy configuration model."""

    model_config = {"populate_by_name": True}

    version: str = Field(default="api.keploy.io/v1beta2", description="Config version")
    name: str = Field(description="Project name")
    app: AppConfig = Field(description="Application configuration")
    test: TestConfig = Field(description="Test configuration")

    @classmethod
    def load(cls, path: str | Path = "keploy.yml") -> "KeployConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to keploy.yml file

        Returns:
            Loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_path = Path(path)
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)

        with config_path.open() as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    def save(self, path: str | Path = "keploy.yml") -> None:
        """Save configuration to YAML file.

        Args:
            path: Path to save configuration
        """
        config_path = Path(path)
        with config_path.open("w") as f:
            yaml.dump(
                self.model_dump(by_alias=True, exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    def add_noise_filter(self, field: str, scope: str = "global") -> None:
        """Add a noise filter to ignore dynamic fields.

        Args:
            field: Field name to filter (e.g., 'timestamp', 'session_id')
            scope: Scope of filter ('global' or test-set name)
        """
        if scope == "global":
            if "global" not in self.test.global_noise:
                self.test.global_noise["global"] = {"body": []}
            if "body" not in self.test.global_noise["global"]:
                self.test.global_noise["global"]["body"] = []
            if field not in self.test.global_noise["global"]["body"]:
                self.test.global_noise["global"]["body"].append(field)
        else:
            if "test-sets" not in self.test.global_noise:
                self.test.global_noise["test-sets"] = {}
            if scope not in self.test.global_noise["test-sets"]:
                self.test.global_noise["test-sets"][scope] = {"body": []}
            if "body" not in self.test.global_noise["test-sets"][scope]:
                self.test.global_noise["test-sets"][scope]["body"] = []
            if field not in self.test.global_noise["test-sets"][scope]["body"]:
                self.test.global_noise["test-sets"][scope]["body"].append(field)


def create_default_config(
    name: str,
    command: str,
    port: int = 8000,
    output_path: str | Path = "keploy.yml",
) -> KeployConfig:
    """Create a default Keploy configuration.

    Args:
        name: Project name
        command: Command to start the application
        port: Application port (default: 8000)
        output_path: Where to save the config (default: keploy.yml)

    Returns:
        Created configuration
    """
    config = KeployConfig(
        name=name,
        app=AppConfig(command=command, port=port),
        test=TestConfig(),
    )
    config.save(output_path)
    return config
