from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class AnimationParams:
    dx: float = 0.0
    dy: float = 0.0


@dataclasses.dataclass(frozen=True)
class Theme:
    dark_mode: bool


@dataclasses.dataclass(frozen=True)
class PanelDimensions:
    width: int
    height: int
    header_height: int
    row_height: int
    rows_visible: int
    detail_height: int
