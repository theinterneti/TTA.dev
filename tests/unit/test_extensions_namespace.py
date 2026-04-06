"""Unit tests for ttadev/primitives/extensions/__init__.py (0% coverage → 90%+)."""

from __future__ import annotations

import pytest


def test_extension_modules_dict_keys() -> None:
    """EXTENSION_MODULES has all expected extension aliases."""
    from ttadev.primitives.extensions import EXTENSION_MODULES

    assert isinstance(EXTENSION_MODULES, dict)
    assert "ace" in EXTENSION_MODULES
    assert "adaptive" in EXTENSION_MODULES
    assert "orchestration" in EXTENSION_MODULES
    assert "research" in EXTENSION_MODULES


def test_extension_modules_values_are_strings() -> None:
    """All EXTENSION_MODULES values are fully-qualified module path strings."""
    from ttadev.primitives.extensions import EXTENSION_MODULES

    for alias, path in EXTENSION_MODULES.items():
        assert isinstance(path, str), f"Expected str for {alias!r}, got {type(path)}"
        assert path.startswith("ttadev."), f"Unexpected path prefix for {alias!r}: {path!r}"


def test_list_extensions_returns_sorted_list() -> None:
    """list_extensions() returns a sorted list of extension names."""
    from ttadev.primitives.extensions import EXTENSION_MODULES, list_extensions

    result = list_extensions()
    assert isinstance(result, list)
    assert result == sorted(result), "list_extensions() must return a sorted list"
    assert set(result) == set(EXTENSION_MODULES.keys())


def test_list_extensions_contains_known_names() -> None:
    """list_extensions() includes all documented extension modules."""
    from ttadev.primitives.extensions import list_extensions

    exts = list_extensions()
    for name in ("ace", "adaptive", "analysis", "apm", "lifecycle"):
        assert name in exts, f"{name!r} missing from list_extensions()"


def test_getattr_lazy_loads_known_module() -> None:
    """Accessing a known extension name via attribute triggers a lazy import."""
    import ttadev.primitives.extensions as ext_ns

    # 'research' is a valid extension; __getattr__ should import it
    module = ext_ns.research  # type: ignore[attr-defined]
    assert module is not None
    assert hasattr(module, "__name__")
    assert "research" in module.__name__


def test_getattr_unknown_name_raises_attribute_error() -> None:
    """Accessing an unknown attribute raises AttributeError."""
    import ttadev.primitives.extensions as ext_ns

    with pytest.raises(AttributeError, match="no attribute"):
        _ = ext_ns.does_not_exist  # type: ignore[attr-defined]


def test_all_exports() -> None:
    """__all__ contains the expected public names."""
    from ttadev.primitives import extensions

    assert "EXTENSION_MODULES" in extensions.__all__
    assert "list_extensions" in extensions.__all__
