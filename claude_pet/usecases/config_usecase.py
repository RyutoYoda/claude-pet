from __future__ import annotations

from claude_pet.domain.value_objects import Theme


class ConfigUsecase:
    def __init__(self, config_repo):
        self._repo = config_repo

    def load_theme(self) -> Theme:
        raw = self._repo.load()
        return Theme(dark_mode=bool(raw.get("dark_mode", False)))

    def toggle_theme(self) -> Theme:
        raw = self._repo.load()
        new_dark = not bool(raw.get("dark_mode", False))
        raw["dark_mode"] = new_dark
        self._repo.save(raw)
        return Theme(dark_mode=new_dark)

    def get_character_image(self) -> str | None:
        return self._repo.load().get("character_image")

    def set_character_image(self, path: str | None) -> None:
        raw = self._repo.load()
        raw["character_image"] = path
        self._repo.save(raw)
