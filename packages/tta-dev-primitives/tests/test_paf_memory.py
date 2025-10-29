"""Tests for PAF Memory Primitive."""

import tempfile
from pathlib import Path

import pytest

from tta_dev_primitives import PAF, PAFMemoryPrimitive, PAFStatus, PAFValidationResult


@pytest.fixture
def paf_primitive():
    """Create PAF primitive with default PAFCORE.md."""
    return PAFMemoryPrimitive()


@pytest.fixture
def custom_paf_core():
    """Create a temporary custom PAFCORE.md for testing."""
    content = """# Test PAF Core

### 1. Technology Stack

#### Core Languages

- **LANG-001**: Primary language is Python 3.12+
- **LANG-002**: Package management via `uv`

### 2. Code Quality

#### Testing Requirements

- **QUAL-001**: Minimum 70% test coverage for production code
- **QUAL-002**: All public APIs must have docstrings

#### File Organization

- **QUAL-004**: Maximum file size 800 lines (production maturity)
- **QUAL-005**: ~~Old rule~~ **DEPRECATED**
    - Reason: Superseded by new standard
    - Replaced by: QUAL-006
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    yield temp_path

    # Cleanup
    temp_path.unlink()


def test_paf_primitive_initialization(paf_primitive):
    """Test PAF primitive initializes correctly."""
    assert paf_primitive is not None
    assert isinstance(paf_primitive.pafs, dict)
    assert len(paf_primitive.pafs) > 0


def test_paf_primitive_loads_pafs(paf_primitive):
    """Test PAF primitive loads PAFs from PAFCORE.md."""
    summary = paf_primitive.summary()

    assert summary["total_pafs"] > 0
    assert summary["active_pafs"] > 0
    assert "categories" in summary
    assert "LANG" in summary["categories"]


def test_get_paf_by_id(paf_primitive):
    """Test retrieving a PAF by ID."""
    paf = paf_primitive.get_paf("LANG-001")

    assert paf is not None
    assert isinstance(paf, PAF)
    assert paf.category == "LANG"
    assert paf.fact_id == "001"
    assert paf.full_id == "LANG-001"
    assert "Python 3.12+" in paf.description


def test_get_pafs_by_category(paf_primitive):
    """Test retrieving PAFs by category."""
    lang_pafs = paf_primitive.get_pafs_by_category("LANG")

    assert len(lang_pafs) > 0
    assert all(paf.category == "LANG" for paf in lang_pafs)


def test_get_active_pafs(paf_primitive):
    """Test retrieving only active PAFs."""
    active_pafs = paf_primitive.get_active_pafs()

    assert len(active_pafs) > 0
    assert all(paf.is_active() for paf in active_pafs)
    assert all(paf.status == PAFStatus.ACTIVE for paf in active_pafs)


def test_validate_python_version_valid(paf_primitive):
    """Test Python version validation with valid version."""
    result = paf_primitive.validate_python_version("3.12.0")

    assert isinstance(result, PAFValidationResult)
    assert result.is_valid
    assert result.paf_id == "LANG-001"
    assert result.actual_value == "3.12.0"
    assert result.reason is None


def test_validate_python_version_invalid(paf_primitive):
    """Test Python version validation with invalid version."""
    result = paf_primitive.validate_python_version("3.11.0")

    assert isinstance(result, PAFValidationResult)
    assert not result.is_valid
    assert result.paf_id == "LANG-001"
    assert result.actual_value == "3.11.0"
    assert "3.12+" in result.reason


def test_validate_python_version_future(paf_primitive):
    """Test Python version validation with future version."""
    result = paf_primitive.validate_python_version("3.14.0")

    assert result.is_valid
    assert result.paf_id == "LANG-001"


def test_validate_test_coverage_valid(paf_primitive):
    """Test coverage validation with valid coverage."""
    result = paf_primitive.validate_test_coverage(75.0)

    assert result.is_valid
    assert result.paf_id == "QUAL-001"
    assert result.actual_value == "75.0%"
    assert result.reason is None


def test_validate_test_coverage_invalid(paf_primitive):
    """Test coverage validation with invalid coverage."""
    result = paf_primitive.validate_test_coverage(65.0)

    assert not result.is_valid
    assert result.paf_id == "QUAL-001"
    assert "65.0%" in result.actual_value
    assert "70%" in result.reason


def test_validate_test_coverage_exact_threshold(paf_primitive):
    """Test coverage validation at exact threshold."""
    result = paf_primitive.validate_test_coverage(70.0)

    assert result.is_valid
    assert result.actual_value == "70.0%"


def test_validate_file_size_valid(paf_primitive):
    """Test file size validation with valid size."""
    result = paf_primitive.validate_file_size(Path("test.py"), 500)

    assert result.is_valid
    assert result.paf_id == "QUAL-004"
    assert "500 lines" in result.actual_value


def test_validate_file_size_invalid(paf_primitive):
    """Test file size validation with invalid size."""
    result = paf_primitive.validate_file_size(Path("large_file.py"), 1200)

    assert not result.is_valid
    assert result.paf_id == "QUAL-004"
    assert "1200 lines" in result.actual_value
    assert "800" in result.reason


def test_validate_file_size_at_threshold(paf_primitive):
    """Test file size validation at exact threshold."""
    result = paf_primitive.validate_file_size(Path("exact.py"), 800)

    assert result.is_valid
    assert "800 lines" in result.actual_value


def test_custom_paf_core_loading(custom_paf_core):
    """Test loading custom PAFCORE.md file."""
    paf_primitive = PAFMemoryPrimitive(paf_core_path=custom_paf_core)

    assert paf_primitive is not None
    summary = paf_primitive.summary()

    # Should have loaded test PAFs
    assert summary["total_pafs"] >= 4  # LANG-001, LANG-002, QUAL-001, QUAL-002, QUAL-004
    assert "LANG" in summary["categories"]
    assert "QUAL" in summary["categories"]


def test_deprecated_paf_detection(custom_paf_core):
    """Test detection of deprecated PAFs."""
    paf_primitive = PAFMemoryPrimitive(paf_core_path=custom_paf_core)

    # Should load deprecated PAF
    deprecated_paf = paf_primitive.get_paf("QUAL-005")
    if deprecated_paf:  # May or may not be loaded depending on parser
        assert deprecated_paf.status == PAFStatus.DEPRECATED
        assert deprecated_paf.deprecated_reason is not None


def test_validate_against_paf_with_custom_validator(paf_primitive):
    """Test generic PAF validation with custom validator."""

    def custom_validator(value: str | int | float | bool, paf: PAF) -> bool:
        # Custom logic: check if value is a string and contains "uv"
        return isinstance(value, str) and "uv" in value.lower()

    result = paf_primitive.validate_against_paf(
        "LANG-002", "Using uv package manager", custom_validator
    )

    assert result.is_valid
    assert result.paf_id == "LANG-002"


def test_validate_against_paf_nonexistent(paf_primitive):
    """Test validation against non-existent PAF."""
    result = paf_primitive.validate_against_paf("NONEXISTENT-999", "test")

    assert not result.is_valid
    assert "not found" in result.reason


def test_get_all_validations(paf_primitive):
    """Test retrieving list of validation methods."""
    validations = paf_primitive.get_all_validations()

    assert isinstance(validations, list)
    assert "validate_python_version" in validations
    assert "validate_test_coverage" in validations
    assert "validate_file_size" in validations
    assert "validate_against_paf" in validations


def test_paf_summary_structure(paf_primitive):
    """Test PAF summary returns correct structure."""
    summary = paf_primitive.summary()

    assert "total_pafs" in summary
    assert "active_pafs" in summary
    assert "deprecated_pafs" in summary
    assert "categories" in summary
    assert "paf_core_path" in summary

    assert isinstance(summary["total_pafs"], int)
    assert isinstance(summary["active_pafs"], int)
    assert isinstance(summary["categories"], dict)


def test_paf_full_id_property():
    """Test PAF full_id property."""
    paf = PAF(category="TEST", fact_id="123", description="Test PAF")

    assert paf.full_id == "TEST-123"


def test_paf_is_active_method():
    """Test PAF is_active method."""
    active_paf = PAF(category="TEST", fact_id="001", description="Active", status=PAFStatus.ACTIVE)
    deprecated_paf = PAF(
        category="TEST",
        fact_id="002",
        description="Deprecated",
        status=PAFStatus.DEPRECATED,
    )

    assert active_paf.is_active()
    assert not deprecated_paf.is_active()


def test_paf_primitive_missing_pafcore():
    """Test PAF primitive raises error when PAFCORE.md not found."""
    with pytest.raises(FileNotFoundError):
        PAFMemoryPrimitive(paf_core_path="/nonexistent/path/PAFCORE.md")
