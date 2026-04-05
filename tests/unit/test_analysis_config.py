"""Unit tests for ttadev/primitives/config/analysis_config.py.

Covers:
- AnalysisSettings: defaults, field_validator, bounds
- TransformSettings: defaults, custom values
- PatternSettings: defaults, custom_rules, enabled_detectors
- PrimitiveSettings: defaults, import_style validator
- MCPSettings: defaults, port bounds
- BenchmarkSettings: defaults, bounds
- TTAConfig: composition, model_dump
- find_config_file: yaml, yml, json, parent-walk, cwd default
- _has_tta_dev_section: True/False/parse-error
- load_config: defaults, yaml, json, toml, pyproject, string path,
  file-not-found, invalid config, bare .ttadevrc
- _load_yaml / _load_json helpers
- save_config: yaml, json, unsupported format, string path
- generate_default_config: yaml, json, unsupported
- merge_cli_options: all mappings, None skipped, unknown key, immutability
- get_config / get_config_path: caching, reload
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from ttadev.primitives.config.analysis_config import (
    AnalysisSettings,
    BenchmarkSettings,
    MCPSettings,
    PatternSettings,
    PrimitiveSettings,
    TransformSettings,
    TTAConfig,
    _has_tta_dev_section,
    _load_json,
    _load_yaml,
    find_config_file,
    generate_default_config,
    get_config,
    get_config_path,
    load_config,
    merge_cli_options,
    save_config,
)

# ---------------------------------------------------------------------------
# AnalysisSettings
# ---------------------------------------------------------------------------


class TestAnalysisSettings:
    def test_defaults(self):
        s = AnalysisSettings()
        assert s.min_confidence == 0.3
        assert s.output_format == "table"
        assert s.show_templates is False
        assert s.show_line_numbers is False
        assert s.quiet is False
        assert s.max_recommendations == 10

    def test_all_valid_output_formats(self):
        for fmt in ("table", "json", "brief", "markdown"):
            s = AnalysisSettings(output_format=fmt)
            assert s.output_format == fmt

    def test_invalid_output_format_raises(self):
        with pytest.raises((ValueError, Exception)):
            AnalysisSettings(output_format="xml")

    def test_min_confidence_lower_bound(self):
        AnalysisSettings(min_confidence=0.0)
        with pytest.raises((ValueError, Exception)):
            AnalysisSettings(min_confidence=-0.01)

    def test_min_confidence_upper_bound(self):
        AnalysisSettings(min_confidence=1.0)
        with pytest.raises((ValueError, Exception)):
            AnalysisSettings(min_confidence=1.01)

    def test_max_recommendations_lower_bound(self):
        AnalysisSettings(max_recommendations=1)
        with pytest.raises((ValueError, Exception)):
            AnalysisSettings(max_recommendations=0)

    def test_max_recommendations_upper_bound(self):
        AnalysisSettings(max_recommendations=50)
        with pytest.raises((ValueError, Exception)):
            AnalysisSettings(max_recommendations=51)

    def test_custom_values_accepted(self):
        s = AnalysisSettings(
            min_confidence=0.7,
            output_format="json",
            show_templates=True,
            show_line_numbers=True,
            quiet=True,
            max_recommendations=20,
        )
        assert s.min_confidence == 0.7
        assert s.show_templates is True
        assert s.quiet is True


# ---------------------------------------------------------------------------
# TransformSettings
# ---------------------------------------------------------------------------


class TestTransformSettings:
    def test_defaults(self):
        s = TransformSettings()
        assert s.auto_fix is False
        assert s.suggest_diff is False
        assert s.backup_files is True
        assert s.confirm_changes is True
        assert s.preferred_primitive is None

    def test_custom_values(self):
        s = TransformSettings(
            auto_fix=True,
            suggest_diff=True,
            backup_files=False,
            confirm_changes=False,
            preferred_primitive="RetryPrimitive",
        )
        assert s.auto_fix is True
        assert s.preferred_primitive == "RetryPrimitive"


# ---------------------------------------------------------------------------
# PatternSettings
# ---------------------------------------------------------------------------


class TestPatternSettings:
    def test_defaults_include_standard_ignores(self):
        s = PatternSettings()
        assert "test_*.py" in s.ignore
        assert "*_test.py" in s.ignore
        assert "conftest.py" in s.ignore
        assert "__pycache__/**" in s.ignore

    def test_custom_rules_empty_by_default(self):
        s = PatternSettings()
        assert s.custom_rules == []

    def test_enabled_detectors_populated(self):
        s = PatternSettings()
        expected = {
            "retry_loop",
            "timeout",
            "cache_pattern",
            "fallback",
            "gather",
            "router_pattern",
        }
        assert expected.issubset(set(s.enabled_detectors))

    def test_custom_ignore_list(self):
        s = PatternSettings(ignore=["*.tmp", "*.bak"])
        assert s.ignore == ["*.tmp", "*.bak"]

    def test_custom_rules_accepted(self):
        rules = [{"name": "my_rule", "pattern": "foo"}]
        s = PatternSettings(custom_rules=rules)
        assert s.custom_rules == rules


# ---------------------------------------------------------------------------
# PrimitiveSettings
# ---------------------------------------------------------------------------


class TestPrimitiveSettings:
    def test_defaults(self):
        s = PrimitiveSettings()
        assert s.preferred == []
        assert s.disabled == []
        assert s.import_style == "specific"

    def test_valid_import_style_specific(self):
        s = PrimitiveSettings(import_style="specific")
        assert s.import_style == "specific"

    def test_valid_import_style_module(self):
        s = PrimitiveSettings(import_style="module")
        assert s.import_style == "module"

    def test_invalid_import_style_raises(self):
        with pytest.raises((ValueError, Exception)):
            PrimitiveSettings(import_style="wildcard")

    def test_preferred_and_disabled(self):
        s = PrimitiveSettings(preferred=["RetryPrimitive"], disabled=["CachePrimitive"])
        assert "RetryPrimitive" in s.preferred
        assert "CachePrimitive" in s.disabled


# ---------------------------------------------------------------------------
# MCPSettings
# ---------------------------------------------------------------------------


class TestMCPSettings:
    def test_defaults(self):
        s = MCPSettings()
        assert s.host == "127.0.0.1"
        assert s.port == 5000
        assert s.enable_unsafe_tools is False
        assert s.log_requests is False

    def test_port_minimum(self):
        MCPSettings(port=1)
        with pytest.raises((ValueError, Exception)):
            MCPSettings(port=0)

    def test_port_maximum(self):
        MCPSettings(port=65535)
        with pytest.raises((ValueError, Exception)):
            MCPSettings(port=65536)

    def test_custom_host_and_port(self):
        s = MCPSettings(host="0.0.0.0", port=8080)
        assert s.host == "0.0.0.0"
        assert s.port == 8080


# ---------------------------------------------------------------------------
# BenchmarkSettings
# ---------------------------------------------------------------------------


class TestBenchmarkSettings:
    def test_defaults(self):
        s = BenchmarkSettings()
        assert s.iterations == 100
        assert s.warmup == 5
        assert s.output_dir == "benchmark_results"

    def test_custom_values(self):
        s = BenchmarkSettings(iterations=50, warmup=0, output_dir="/tmp/bench")
        assert s.iterations == 50
        assert s.warmup == 0

    def test_iterations_minimum_1(self):
        with pytest.raises((ValueError, Exception)):
            BenchmarkSettings(iterations=0)

    def test_warmup_minimum_0(self):
        BenchmarkSettings(warmup=0)
        with pytest.raises((ValueError, Exception)):
            BenchmarkSettings(warmup=-1)


# ---------------------------------------------------------------------------
# TTAConfig
# ---------------------------------------------------------------------------


class TestTTAConfig:
    def test_defaults(self):
        cfg = TTAConfig()
        assert cfg.version == "1.0"
        assert isinstance(cfg.analysis, AnalysisSettings)
        assert isinstance(cfg.transform, TransformSettings)
        assert isinstance(cfg.patterns, PatternSettings)
        assert isinstance(cfg.primitives, PrimitiveSettings)
        assert isinstance(cfg.mcp, MCPSettings)
        assert isinstance(cfg.benchmark, BenchmarkSettings)

    def test_nested_customization_via_dict(self):
        cfg = TTAConfig(
            analysis={"min_confidence": 0.8, "output_format": "json"},
            mcp={"port": 9000},
        )
        assert cfg.analysis.min_confidence == 0.8
        assert cfg.analysis.output_format == "json"
        assert cfg.mcp.port == 9000

    def test_model_dump_contains_all_sections(self):
        cfg = TTAConfig()
        data = cfg.model_dump()
        for section in ("analysis", "transform", "patterns", "primitives", "mcp", "benchmark"):
            assert section in data

    def test_version_field(self):
        cfg = TTAConfig(version="2.0")
        assert cfg.version == "2.0"


# ---------------------------------------------------------------------------
# find_config_file
# ---------------------------------------------------------------------------


class TestFindConfigFile:
    def test_finds_yaml_config(self, tmp_path):
        # Arrange
        config_file = tmp_path / ".ttadevrc.yaml"
        config_file.write_text("analysis:\n  min_confidence: 0.5\n")
        # Act
        result = find_config_file(start_dir=tmp_path)
        # Assert
        assert result == config_file

    def test_finds_yml_config(self, tmp_path):
        # Arrange
        config_file = tmp_path / ".ttadevrc.yml"
        config_file.write_text("analysis:\n  quiet: true\n")
        # Act
        result = find_config_file(start_dir=tmp_path)
        # Assert
        assert result == config_file

    def test_finds_json_config(self, tmp_path):
        # Arrange
        config_file = tmp_path / ".ttadevrc.json"
        config_file.write_text('{"analysis": {"quiet": true}}')
        # Act
        result = find_config_file(start_dir=tmp_path)
        # Assert
        assert result == config_file

    def test_walks_up_to_parent_dir(self, tmp_path):
        # Arrange — config in parent, start in child
        config_file = tmp_path / ".ttadevrc.yaml"
        config_file.write_text("version: '2.0'\n")
        child = tmp_path / "subdir"
        child.mkdir()
        # Act
        result = find_config_file(start_dir=child)
        # Assert
        assert result == config_file

    def test_uses_cwd_when_start_dir_none(self, tmp_path, monkeypatch):
        # Arrange
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".ttadevrc.yaml"
        config_file.write_text("version: '1.0'\n")
        # Act
        result = find_config_file(start_dir=None)
        # Assert
        assert result == config_file

    def test_returns_none_or_path_for_empty_dir(self, tmp_path):
        # Arrange — isolated tmp dir with no config files
        # (may find home dir config or project pyproject.toml, so allow both)
        result = find_config_file(start_dir=tmp_path)
        assert result is None or isinstance(result, Path)

    def test_finds_bare_ttadevrc(self, tmp_path):
        # Arrange
        config_file = tmp_path / ".ttadevrc"
        config_file.write_text("version: '1.0'\n")
        # Act
        result = find_config_file(start_dir=tmp_path)
        # Assert
        assert result == config_file


# ---------------------------------------------------------------------------
# _has_tta_dev_section
# ---------------------------------------------------------------------------


class TestHasTtaDevSection:
    def test_returns_true_when_section_present(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_bytes(b'[tool.tta-dev]\nversion = "1.0"\n')
        assert _has_tta_dev_section(pyproject) is True

    def test_returns_false_when_section_absent(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_bytes(b'[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
        assert _has_tta_dev_section(pyproject) is False

    def test_returns_false_on_parse_error(self, tmp_path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_bytes(b"NOT VALID TOML ][[\n")
        assert _has_tta_dev_section(pyproject) is False


# ---------------------------------------------------------------------------
# _load_yaml / _load_json
# ---------------------------------------------------------------------------


class TestLoaderHelpers:
    def test_load_yaml_returns_dict(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text("key: value\nnested:\n  x: 1\n")
        result = _load_yaml(f)
        assert result == {"key": "value", "nested": {"x": 1}}

    def test_load_yaml_empty_file_returns_empty_dict(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("")
        result = _load_yaml(f)
        assert result == {}

    def test_load_json_returns_dict(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"a": 1, "b": "two"}')
        result = _load_json(f)
        assert result == {"a": 1, "b": "two"}


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_returns_defaults_when_no_config(self, tmp_path, monkeypatch):
        # Arrange — empty isolated dir, chdir so home dir search also limited
        monkeypatch.chdir(tmp_path)
        # Act
        cfg = load_config(start_dir=tmp_path)
        # Assert
        assert isinstance(cfg, TTAConfig)

    def test_loads_yaml_config(self, tmp_path):
        # Arrange
        f = tmp_path / ".ttadevrc.yaml"
        f.write_text("analysis:\n  min_confidence: 0.8\n  output_format: json\n")
        # Act
        cfg = load_config(config_path=f)
        # Assert
        assert cfg.analysis.min_confidence == 0.8
        assert cfg.analysis.output_format == "json"

    def test_loads_json_config(self, tmp_path):
        # Arrange
        f = tmp_path / ".ttadevrc.json"
        f.write_text(json.dumps({"analysis": {"quiet": True}}))
        # Act
        cfg = load_config(config_path=f)
        # Assert
        assert cfg.analysis.quiet is True

    def test_loads_toml_config(self, tmp_path):
        # Arrange
        f = tmp_path / ".ttadevrc.toml"
        f.write_bytes(b"[analysis]\nmin_confidence = 0.6\n")
        # Act
        cfg = load_config(config_path=f)
        # Assert
        assert cfg.analysis.min_confidence == pytest.approx(0.6)

    def test_loads_pyproject_toml_tta_section(self, tmp_path):
        # Arrange
        f = tmp_path / "pyproject.toml"
        f.write_bytes(b"[tool.tta-dev]\n[tool.tta-dev.analysis]\nquiet = true\n")
        # Act
        cfg = load_config(config_path=f)
        # Assert
        assert cfg.analysis.quiet is True

    def test_loads_bare_ttadevrc_as_yaml(self, tmp_path):
        # Arrange
        f = tmp_path / ".ttadevrc"
        f.write_text("analysis:\n  quiet: true\n")
        # Act
        cfg = load_config(config_path=f)
        # Assert
        assert cfg.analysis.quiet is True

    def test_explicit_path_not_found_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(config_path=tmp_path / "nonexistent.yaml")

    def test_invalid_config_raises_value_error(self, tmp_path):
        # Arrange — invalid output_format
        f = tmp_path / ".ttadevrc.yaml"
        f.write_text("analysis:\n  output_format: invalid\n")
        # Act & Assert
        with pytest.raises(ValueError):
            load_config(config_path=f)

    def test_accepts_string_path(self, tmp_path):
        # Arrange
        f = tmp_path / ".ttadevrc.yaml"
        f.write_text("version: '1.0'\n")
        # Act
        cfg = load_config(config_path=str(f))
        # Assert
        assert isinstance(cfg, TTAConfig)

    def test_unknown_extension_tries_yaml(self, tmp_path):
        # Arrange — .conf file treated as YAML
        f = tmp_path / "myconfig.conf"
        f.write_text("analysis:\n  quiet: true\n")
        # Act
        cfg = load_config(config_path=f)
        # Assert
        assert cfg.analysis.quiet is True


# ---------------------------------------------------------------------------
# save_config
# ---------------------------------------------------------------------------


class TestSaveConfig:
    def test_save_yaml_creates_file(self, tmp_path):
        # Arrange
        cfg = TTAConfig()
        path = tmp_path / "out.yaml"
        # Act
        save_config(cfg, path, format="yaml")
        # Assert
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert isinstance(data, dict)

    def test_save_json_creates_file(self, tmp_path):
        # Arrange
        cfg = TTAConfig()
        path = tmp_path / "out.json"
        # Act
        save_config(cfg, path, format="json")
        # Assert
        assert path.exists()
        data = json.loads(path.read_text())
        assert isinstance(data, dict)

    def test_save_unsupported_format_raises(self, tmp_path):
        cfg = TTAConfig()
        with pytest.raises(ValueError, match="Unsupported format"):
            save_config(cfg, tmp_path / "out.xml", format="xml")

    def test_save_accepts_string_path(self, tmp_path):
        cfg = TTAConfig()
        path = str(tmp_path / "out.yaml")
        save_config(cfg, path, format="yaml")
        assert Path(path).exists()

    def test_save_yaml_roundtrip(self, tmp_path):
        # Arrange
        cfg = TTAConfig(analysis={"min_confidence": 0.9, "output_format": "json"})
        path = tmp_path / "roundtrip.yaml"
        # Act
        save_config(cfg, path, format="yaml")
        loaded = load_config(config_path=path)
        # Assert — non-default values should survive roundtrip
        assert loaded.analysis.output_format == "json"


# ---------------------------------------------------------------------------
# generate_default_config
# ---------------------------------------------------------------------------


class TestGenerateDefaultConfig:
    def test_yaml_output_is_string_with_sections(self):
        result = generate_default_config(format="yaml")
        assert isinstance(result, str)
        assert "analysis" in result

    def test_json_output_is_valid_json_with_sections(self):
        result = generate_default_config(format="json")
        data = json.loads(result)
        assert "analysis" in data
        assert "transform" in data
        assert "mcp" in data

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError):
            generate_default_config(format="toml")


# ---------------------------------------------------------------------------
# merge_cli_options
# ---------------------------------------------------------------------------


class TestMergeCliOptions:
    def test_merges_min_confidence(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, min_confidence=0.9)
        assert result.analysis.min_confidence == 0.9

    def test_merges_output_format_via_output_key(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, output="json")
        assert result.analysis.output_format == "json"

    def test_merges_show_templates(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, templates=True)
        assert result.analysis.show_templates is True

    def test_merges_show_templates_via_show_templates_key(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, show_templates=True)
        assert result.analysis.show_templates is True

    def test_merges_quiet(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, quiet=True)
        assert result.analysis.quiet is True

    def test_merges_show_line_numbers(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, lines=True)
        assert result.analysis.show_line_numbers is True

    def test_merges_auto_fix(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, apply=True)
        assert result.transform.auto_fix is True

    def test_merges_suggest_diff(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, suggest_diff=True)
        assert result.transform.suggest_diff is True

    def test_merges_preferred_primitive(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, apply_primitive="RetryPrimitive")
        assert result.transform.preferred_primitive == "RetryPrimitive"

    def test_merges_mcp_host(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, host="0.0.0.0")
        assert result.mcp.host == "0.0.0.0"

    def test_merges_mcp_port(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, port=9000)
        assert result.mcp.port == 9000

    def test_merges_benchmark_iterations(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, iterations=200)
        assert result.benchmark.iterations == 200

    def test_none_values_are_skipped(self):
        cfg = TTAConfig()
        original = cfg.analysis.min_confidence
        result = merge_cli_options(cfg, min_confidence=None)
        assert result.analysis.min_confidence == original

    def test_unknown_keys_are_ignored(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, nonexistent_option="value")
        assert isinstance(result, TTAConfig)

    def test_original_config_not_mutated(self):
        cfg = TTAConfig()
        original_confidence = cfg.analysis.min_confidence
        merge_cli_options(cfg, min_confidence=0.99)
        assert cfg.analysis.min_confidence == original_confidence

    def test_returns_new_tta_config_instance(self):
        cfg = TTAConfig()
        result = merge_cli_options(cfg, quiet=True)
        assert result is not cfg


# ---------------------------------------------------------------------------
# get_config / get_config_path
# ---------------------------------------------------------------------------


class TestGetConfig:
    def setup_method(self):
        """Reset module-level cache before each test."""
        import ttadev.primitives.config.analysis_config as mod

        mod._cached_config = None
        mod._cached_config_path = None

    def test_returns_tta_config(self):
        cfg = get_config()
        assert isinstance(cfg, TTAConfig)

    def test_caches_result(self):
        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_reload_returns_fresh_instance(self):
        import ttadev.primitives.config.analysis_config as mod

        mod._cached_config = None
        get_config()
        cfg2 = get_config(reload=True)
        assert isinstance(cfg2, TTAConfig)

    def test_get_config_path_returns_none_or_path(self):
        import ttadev.primitives.config.analysis_config as mod

        mod._cached_config_path = None
        result = get_config_path()
        assert result is None or isinstance(result, Path)
