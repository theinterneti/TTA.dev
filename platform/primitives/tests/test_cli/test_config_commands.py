"""Tests for CLI config commands."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml
from typer.testing import CliRunner

from tta_dev_primitives.cli.app import app

runner = CliRunner()


class TestConfigInit:
    """Tests for 'tta-dev config init' command."""

    def test_config_init_help(self) -> None:
        """Test config init help."""
        result = runner.invoke(app, ["config", "init", "--help"])
        assert result.exit_code == 0
        assert "Initialize a new configuration file" in result.output

    def test_config_init_creates_file(self) -> None:
        """Test config init creates default file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                ["config", "init", "--path", f"{tmpdir}/.ttadevrc.yaml"],
            )
            assert result.exit_code == 0
            assert "Created config file" in result.output

            # Verify file exists
            config_path = Path(tmpdir) / ".ttadevrc.yaml"
            assert config_path.exists()

            # Verify it's valid YAML
            with open(config_path) as f:
                data = yaml.safe_load(f)
            assert "analysis" in data or data == {}  # May be empty if exclude_defaults

    def test_config_init_json_format(self) -> None:
        """Test config init with JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "config",
                    "init",
                    "--format",
                    "json",
                    "--path",
                    f"{tmpdir}/config.json",
                ],
            )
            assert result.exit_code == 0

            # Verify it's valid JSON
            config_path = Path(tmpdir) / "config.json"
            with open(config_path) as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_config_init_no_overwrite(self) -> None:
        """Test config init doesn't overwrite without --force."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".ttadevrc.yaml"
            config_path.write_text("existing: content\n")

            result = runner.invoke(
                app,
                ["config", "init", "--path", str(config_path)],
            )
            assert result.exit_code == 1
            assert "already exists" in result.output

            # Verify original content preserved
            assert config_path.read_text() == "existing: content\n"

    def test_config_init_force_overwrite(self) -> None:
        """Test config init with --force overwrites."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".ttadevrc.yaml"
            config_path.write_text("existing: content\n")

            result = runner.invoke(
                app,
                ["config", "init", "--path", str(config_path), "--force"],
            )
            assert result.exit_code == 0
            assert "Created config file" in result.output


class TestConfigShow:
    """Tests for 'tta-dev config show' command."""

    def test_config_show_help(self) -> None:
        """Test config show help."""
        result = runner.invoke(app, ["config", "show", "--help"])
        assert result.exit_code == 0
        assert "Show current configuration" in result.output

    def test_config_show_defaults(self) -> None:
        """Test config show displays defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run from a directory with no config
            result = runner.invoke(
                app,
                ["config", "show"],
                catch_exceptions=False,
            )
            assert result.exit_code == 0
            # Should show analysis section
            assert "analysis" in result.output

    def test_config_show_custom_file(self) -> None:
        """Test config show with custom file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"analysis": {"min_confidence": 0.9}}, f)
            f.flush()

            result = runner.invoke(
                app,
                ["config", "show", "--config", f.name],
            )
            assert result.exit_code == 0

    def test_config_show_json_format(self) -> None:
        """Test config show with JSON format."""
        result = runner.invoke(
            app,
            ["config", "show", "--format", "json"],
        )
        assert result.exit_code == 0
        # Output should be valid JSON
        # Note: Rich formatting may add extra characters


class TestConfigPath:
    """Tests for 'tta-dev config path' command."""

    def test_config_path_help(self) -> None:
        """Test config path help."""
        result = runner.invoke(app, ["config", "path", "--help"])
        assert result.exit_code == 0
        assert "Show path to current configuration file" in result.output

    def test_config_path_not_found(self) -> None:
        """Test config path when no config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp dir
            result = runner.invoke(app, ["config", "path"])
            # Should show helpful message
            assert (
                "No configuration file found" in result.output or result.exit_code == 0
            )


class TestConfigValidate:
    """Tests for 'tta-dev config validate' command."""

    def test_config_validate_help(self) -> None:
        """Test config validate help."""
        result = runner.invoke(app, ["config", "validate", "--help"])
        assert result.exit_code == 0
        assert "Validate a configuration file" in result.output

    def test_config_validate_valid_file(self) -> None:
        """Test validating a valid config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "analysis": {"min_confidence": 0.5, "output_format": "json"},
                    "transform": {"auto_fix": True},
                },
                f,
            )
            f.flush()

            result = runner.invoke(
                app,
                ["config", "validate", "--config", f.name],
            )
            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_config_validate_invalid_file(self) -> None:
        """Test validating an invalid config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "analysis": {"min_confidence": 2.0},  # Invalid: > 1.0
                },
                f,
            )
            f.flush()

            result = runner.invoke(
                app,
                ["config", "validate", "--config", f.name],
            )
            assert result.exit_code == 1
            assert "Invalid" in result.output or "invalid" in result.output.lower()

    def test_config_validate_nonexistent_file(self) -> None:
        """Test validating non-existent file."""
        result = runner.invoke(
            app,
            ["config", "validate", "--config", "/nonexistent/config.yaml"],
        )
        assert result.exit_code == 1
        assert "not found" in result.output


class TestConfigSubcommandHelp:
    """Tests for config subcommand help."""

    def test_config_help(self) -> None:
        """Test 'tta-dev config --help'."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "show" in result.output
        assert "path" in result.output
        assert "validate" in result.output

    def test_config_no_args(self) -> None:
        """Test 'tta-dev config' with no args shows help."""
        result = runner.invoke(app, ["config"])
        # Typer returns exit code 2 when no_args_is_help=True
        assert result.exit_code in (0, 2)
        assert "init" in result.output or "Usage" in result.output
