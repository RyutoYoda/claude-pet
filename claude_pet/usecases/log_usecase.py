from __future__ import annotations

import datetime

from claude_pet.domain.entities import LogEntry


class LogUsecase:
    MAX_LOGS = 50

    def __init__(self) -> None:
        self._logs: list[LogEntry] = []

    @property
    def logs(self) -> list[LogEntry]:
        return list(self._logs)

    def add(self, message: str) -> LogEntry:
        entry = LogEntry(
            timestamp=datetime.datetime.now().strftime("%H:%M"),
            message=message,
        )
        self._logs.insert(0, entry)
        if len(self._logs) > self.MAX_LOGS:
            self._logs.pop()
        return entry

    def delete(self, index: int) -> bool:
        if 0 <= index < len(self._logs):
            self._logs.pop(index)
            return True
        return False

    def display_text(self, entry: LogEntry, max_chars: int = 15) -> str:
        msg = entry.message[:14] + "…" if len(entry.message) > 15 else entry.message
        return msg.replace("\n", " ")
