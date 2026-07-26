from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class LogEntry:
    timestamp: str
    message: str


@dataclasses.dataclass(frozen=True)
class Notification:
    state: str
    message: str
