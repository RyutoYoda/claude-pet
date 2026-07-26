from __future__ import annotations

import json
from pathlib import Path

_DEFAULTS: dict[str, object] = {
    "character_image": None,
    "dark_mode": True,
}


class ConfigRepo:
    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            path = Path.home() / "Library" / "Preferences" / "claude-pet.json"
        self._path = path

    def load(self) -> dict[str, object]:
        result = dict(_DEFAULTS)
        try:
            data = json.loads(self._path.read_text())
            result.update(data)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return result

    def save(self, config: dict[str, object]) -> None:
        merged = dict(_DEFAULTS)
        merged.update(config)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(merged, indent=2))
