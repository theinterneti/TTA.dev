"""Unit tests for __main__.py entry point — Task 8."""

import socket

from ttadev.observability.__main__ import _port_in_use


def test_port_in_use_detects_occupied_port() -> None:
    # Bind a socket, then check
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("localhost", 0))
        s.listen(1)
        port = s.getsockname()[1]
        assert _port_in_use(port) is True


def test_port_in_use_detects_free_port() -> None:
    # Find a port that is definitely free
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        port = s.getsockname()[1]
    # Socket is now closed — port is free
    assert _port_in_use(port) is False
