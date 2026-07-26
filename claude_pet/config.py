from __future__ import annotations

from claude_pet.infrastructure.config_repo import ConfigRepo

_repo = ConfigRepo()


def load() -> dict[str, object]:
    return _repo.load()


def save(config: dict[str, object]) -> None:
    _repo.save(config)
