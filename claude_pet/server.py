from __future__ import annotations

from collections.abc import Callable

from claude_pet.infrastructure.http_server import HttpServer

_server = HttpServer()


def start(callback: Callable[[str, str], None]) -> None:
    _server.start(callback)
