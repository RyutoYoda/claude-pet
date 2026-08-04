from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class LogEntry:
    timestamp: str
    message: str
    cwd: str = ""
    terminal_pid: int = 0


@dataclasses.dataclass(frozen=True)
class Notification:
    state: str
    message: str
