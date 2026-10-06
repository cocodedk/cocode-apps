import socket

import pytest


def test_non_loopback_socket_is_refused():
    with pytest.raises(RuntimeError, match="offline"):
        socket.create_connection(("192.0.2.1", 80), timeout=1)
