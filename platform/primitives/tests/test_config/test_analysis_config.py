"""Tests for TTA.dev configuration management."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from tta_dev_primitives.config import (
    AnalysisSettings,
    MCPSettings,
    PatternSettings,
    PrimitiveSettings,
    TransformSettings,
    TTAConfig,
    find_config_file,
    generate_default_config,
    load_config,
    merge_cli_options,
    save_config,
)


class TestTTAConfig:
    """Tests for TTAConfig model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = TTAConfig()

        assert config.version == "1.0"
        assert config.analysis.min_confidence == 0.3
        assert config.analysis.output_format == "table"
        assert config.transform.auto_fix is False
        assert config.transform.backup_files is True
        assert config.mcp.port == 5000

    def test_config_from_dict(self) -> None:
        """Test creating config from dictionary."""
        data = {
            "analysis": {
                "min_confidence": 0.5,
                "output_format": "json",
            },
            "transform": {
                "auto_fix": True,
            },
        }

        config = TTAConfig(**data)

        assert config.analysis.min_confidence == 0.5
        assert config.analysis.output_format == "json"
        assert config.transform.auto_fix is True
        # Defaults should still be set
        assert config.transform.backup_files is True

    def test_config_validation_min_confidence(self) -> None:
        """Test min_confidence validation."""
        # Valid values
        config = TTAConfig(analysis=AnalysisSettings(min_confidence=0.0))
        assert config.analysis.min_confidence == 0.0

        config = TTAConfig(analysis=AnalysisSettings(min_confidence=1.0))
        assert config.analysis.min_confidence == 1.0

        # Invalid values
        with pytest.raises(ValueError):
            TTAConfig(analysis=AnalysisSettings(min_confidence=-0.1))

        with pytest.raises(ValueError):
            TTAConfig(analysis=AnalysisSettings(min_confidence=1.5))

    def test_config_validation_output_format(self) -> None:
        """Test output_format validation."""
        valid_formats = ["table", "json", "brief", "markdown"]
        for fmt in valid_formats:
            config = TTAConfig(analysis=AnalysisSettings(output_format=fmt))
            assert config.analysis.output_format == fmt

        with pytest.raises(ValueError):
            TTAConfig(analysis=AnalysisSettings(output_format="invalid"))

    def test_config_validation_import_style(self) -> None:
        """Test import_style validation."""
        valid_styles = ["specific", "module"]
        for style in valid_styles:
            config = TTAConfig(primitives=PrimitiveSettings(import_style=style))
            assert config.primitives.import_style == style

        with pytest.raises(ValueError):
            TTAConfig(primitives=PrimitiveSettings(import_style="invalid"))


class TestAnalysisSettings:
    """Tests for AnalysisSettings model."""

    def test_defaults(self) -> None:
        """Test default analysis settings."""
        settings = AnalysisSettings()

        assert settings.min_confidence == 0.3
        assert settings.output_format == "table"
        assert settings.show_templates is False
        assert settings.show_line_numbers is False
        assert settings.quiet is False
        assert settings.max_recommendations == 10

    def test_max_recommendations_bounds(self) -> None:
        """Test max_recommendations validation."""
        settings = AnalysisSettings(max_recommendations=1)
        assert settings.max_recommendations == 1

        settings = AnalysisSettings(max_recommendations=50)
        assert settings.max_recommendations == 50

        with pytest.raises(ValueError):
            AnalysisSettings(max_recommendations=0)

        with pytest.raises(ValueError):
            AnalysisSettings(max_recommendations=51)


class TestTransformSettings:
    """Tests for TransformSettings model."""

    def test_defaults(self) -> None:
        """Test default transform settings."""
        settings = TransformSettings()

        assert settings.auto_fix is False
        assert settings.suggest_diff is False
        assert settings.backup_files is True
        assert settings.confirm_changes is True
        assert settings.preferred_primitive is None


class TestPatternSettings:
    """Tests for PatternSettings model."""

    def test_default_ignore_patterns(self) -> None:
        """Test default ignore patterns."""
        settings = PatternSettings()

        assert "test_*.py" in settings.ignore
        assert "*_test.py" in settings.ignore
        assert "__pycache__/**" in settings.ignore
        assert ".git/**" in settings.ignore
        assert ".venv/**" in settings.ignore

    def test_default_detectors(self) -> None:
        """Test default enabled detectors."""
        settings = PatternSettings()

        expected_detectors = [
            "retry_loop",
            "timeout",
            "cache_pattern",
            "fallback",
            "gather",
            "router_pattern",
        ]
        assert settings.enabled_detectors == expected_detectors


class TestMCPSettings:
    """Tests for MCPSettings model."""

    def test_defaults(self) -> None:
        """Test default MCP settings."""
        settings = MCPSettings()

        assert settings.host == "127.0.0.1"
        assert settings.port == 5000
        assert settings.enable_unsafe_tools is False
        assert settings.log_requests is False

    def test_port_validation(self) -> None:
        """Test port validation."""
        settings = MCPSettings(port=1)
        assert settings.port == 1

        settings = MCPSettings(port=65535)
        assert settings.port == 65535

        with pytest.raises(ValueError):
            MCPSettings(port=0)

        with pytest.raises(ValueError):
            MCPSettings(port=65536)


class TestConfigLoading:
    """Tests for configuration file loading."""

    def test_load_yaml_config(self) -> None:
        """Test loading YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "analysis": {"min_confidence": 0.7},
                    "transform": {"auto_fix": True},
                },
                f,
            )
            f.flush()

            config = load_config(f.name)

            assert config.analysis.min_confidence == 0.7
            assert config.transform.auto_fix is True

    def test_load_json_config(self) -> None:
        """Test loading JSON configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "analysis": {"min_confidence": 0.6, "output_format": "json"},
                    "mcp": {"port": 8080},
                },
                f,
            )
            f.flush()

            config = load_config(f.name)

            assert config.analysis.min_confidence == 0.6
            assert config.analysis.output_format == "json"
            assert config.mcp.port == 8080

    def test_load_nonexistent_file(self) -> None:
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_invalid_yaml(self) -> None:
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()

            with pytest.raises(ValueError):
                load_config(f.name)

    def test_load_invalid_values(self) -> None:
        """Test loading config with invalid values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "analysis": {"min_confidence": 2.0},  # Invalid
                },
                f,
            )
            f.flush()

            with pytest.raises(ValueError):
                load_config(f.name)

    def test_load_default_when_not_found(self) -> None:
        """Test default config when no file found."""
        # Use a temp directory with no config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(start_dir=Path(tmpdir))
            assert config == TTAConfig()


class TestConfigSaving:
    """Tests for configuration file saving."""

    def test_save_yaml_config(self) -> None:
        """Test saving YAML configuration."""
        config = TTAConfig(
            analysis=AnalysisSettings(min_confidence=0.8),
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            save_config(config, f.name, format="yaml")

            # Reload and verify
            with open(f.name) as rf:
                data = yaml.safe_load(rf)

            assert data["analysis"]["min_confidence"] == 0.8

    def test_save_json_config(self) -> None:
        """Test saving JSON configuration."""
        config = TTAConfig(
            mcp=MCPSettings(port=9000),
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            save_config(config, f.name, format="json")

            # Reload and verify
            with open(f.name) as rf:
                data = json.load(rf)

            assert data["mcp"]["port"] == 9000


class TestConfigMerging:
    """Tests for CLI option merging."""

    def test_merge_min_confidence(self) -> None:
        """Test merging min_confidence CLI option."""
        base_config = TTAConfig()
        merged = merge_cli_options(base_config, min_confidence=0.9)

        assert merged.analysis.min_confidence == 0.9
        # Other values unchanged
        assert merged.analysis.output_format == "table"

    def test_merge_output_format(self) -> None:
        """Test merging output format."""
        base_config = TTAConfig()
        merged = merge_cli_options(base_config, output="json")

        assert merged.analysis.output_format == "json"

    def test_merge_multiple_options(self) -> None:
        """Test merging multiple CLI options."""
        base_config = TTAConfig()
        merged = merge_cli_options(
            base_config,
            min_confidence=0.5,
            output="json",
            quiet=True,
            apply=True,
            port=8080,
        )

        assert merged.analysis.min_confidence == 0.5
        assert merged.analysis.output_format == "json"
        assert merged.analysis.quiet is True
        assert merged.transform.auto_fix is True
        assert merged.mcp.port == 8080

    def test_merge_none_values_ignored(self) -> None:
        """Test that None values don't override config."""
        base_config = TTAConfig(
            analysis=AnalysisSettings(min_confidence=0.7),
        )
        merged = merge_cli_options(
            base_config,
            min_confidence=None,
            output=None,
        )

        assert merged.analysis.min_confidence == 0.7
        assert merged.analysis.output_format == "table"


class TestConfigFinding:
    """Tests for config file discovery."""

    def test_find_config_in_current_dir(self) -> None:
        """Test finding config in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".ttadevrc.yaml"
            config_path.write_text("version: '1.0'\n")

            found = find_config_file(Path(tmpdir))
            assert found == config_path

    def test_find_config_with_different_extensions(self) -> None:
        """Test finding config with different extensions."""
        extensions = [".yaml", ".yml", ".json", ".toml", ""]

        for ext in extensions:
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / f".ttadevrc{ext}"
                if ext == ".json":
                    config_path.write_text("{}")
                else:
                    config_path.write_text("version: '1.0'\n")

                found = find_config_file(Path(tmpdir))
                assert found is not None


class TestGenerateDefaultConfig:
    """Tests for default config generation."""

    def test_generate_yaml(self) -> None:
        """Test generating YAML default config."""
        output = generate_default_config(format="yaml")

        assert "analysis:" in output
        assert "min_confidence:" in output
        assert "transform:" in output
        assert "patterns:" in output

    def test_generate_json(self) -> None:
        """Test generating JSON default config."""
        output = generate_default_config(format="json")

        data = json.loads(output)
        assert "analysis" in data
        assert "transform" in data
        assert "patterns" in data

    def test_generate_invalid_format(self) -> None:
        """Test generating with invalid format."""
        with pytest.raises(ValueError):
            generate_default_config(format="invalid")
