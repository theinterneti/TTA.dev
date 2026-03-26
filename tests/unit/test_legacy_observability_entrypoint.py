"""Unit tests for legacy observability entrypoint deprecation."""

from unittest.mock import patch

from ttadev.ui.observability_server import warn_deprecated_entrypoint


def test_warn_deprecated_entrypoint_emits_warning() -> None:
    """Legacy observability entrypoint should emit a deprecation warning."""
    with patch("ttadev.ui.observability_server.warnings.warn") as mock_warn:
        with patch("sys.stderr"):
            warn_deprecated_entrypoint()

    mock_warn.assert_called_once()
    message = mock_warn.call_args.args[0]
    assert "deprecated" in message.lower()
    assert "python -m ttadev.observability" in message
