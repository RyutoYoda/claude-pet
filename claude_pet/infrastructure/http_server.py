from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer

from claude_pet.constants import PORT


class _Handler(BaseHTTPRequestHandler):
    callback: Callable[[str, str], None] | None = None

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
        if _Handler.callback:
            _Handler.callback(data.get("state", "done"), data.get("message", ""))

    def log_message(self, fmt: str, *args: object) -> None:
        pass


class HttpServer:
    def start(self, callback: Callable[[str, str], None]) -> None:
        _Handler.callback = callback
        server = HTTPServer(("127.0.0.1", PORT), _Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
