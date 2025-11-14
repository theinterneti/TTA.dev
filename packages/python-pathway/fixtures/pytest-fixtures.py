"""Pytest fixtures for the python-pathway

These fixtures are minimal, uv-aware helpers intended for local testing and CI.
"""
from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return repository root path for tests that need to locate files."""
    return Path(__file__).resolve().parents[3]


@pytest.fixture
def sample_config(tmp_path, project_root: Path):
    """Provide a tiny sample config file for tests that expect config on disk."""
    p = tmp_path / "config.toml"
    p.write_text("[tool.sample]\nvalue = 1\n")
    return p


def test_fixtures_importable(project_root, sample_config):
    # simple smoke test to ensure fixtures import and run
    assert project_root.exists()
    assert sample_config.exists()
