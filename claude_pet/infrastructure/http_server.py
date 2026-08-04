from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer

from claude_pet.constants import PORT


class _Handler(BaseHTTPRequestHandler):
    notify_callback: Callable[[str, str, str, int], None] | None = None
    permission_callback: Callable[[str, str, str, str, int], None] | None = None
    decisions: dict[str, str] = {}
    last_poll: dict[str, float] = {}

    def _send_json(self, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if self.path == "/permission":
            request_id = str(data.get("id", ""))
            _Handler.decisions.pop(request_id, None)
            _Handler.last_poll[request_id] = time.time()
            self._send_json({"ok": True})
            if _Handler.permission_callback and request_id:
                _Handler.permission_callback(
                    request_id,
                    str(data.get("tool", "Unknown")),
                    str(data.get("detail", "")),
                    str(data.get("cwd", "")),
                    int(data.get("terminal_pid", 0)),
                )
            return

        # /notify（後方互換のためパス未指定の POST も通知として扱う）
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
        if _Handler.notify_callback:
            _Handler.notify_callback(
                data.get("state", "done"),
                data.get("message", ""),
                data.get("cwd", ""),
                int(data.get("terminal_pid", 0)),
            )

    def do_GET(self) -> None:
        if self.path.startswith("/permission/"):
            request_id = self.path.rsplit("/", 1)[-1]
            _Handler.last_poll[request_id] = time.time()
            self._send_json({"decision": _Handler.decisions.get(request_id)})
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        pass


class HttpServer:
    def start(
        self,
        callback: Callable[[str, str, str, int], None],
        permission_callback: Callable[[str, str, str, str, int], None] | None = None,
    ) -> None:
        _Handler.notify_callback = callback
        _Handler.permission_callback = permission_callback
        server = HTTPServer(("127.0.0.1", PORT), _Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()

    def resolve_permission(self, request_id: str, action: str) -> None:
        _Handler.decisions[request_id] = action

    def last_poll_at(self, request_id: str) -> float:
        return _Handler.last_poll.get(request_id, 0.0)
