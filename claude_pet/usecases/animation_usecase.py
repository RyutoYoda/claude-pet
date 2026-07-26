from __future__ import annotations

import math

from claude_pet.domain.enums import PetState
from claude_pet.domain.value_objects import AnimationParams


class AnimationUsecase:
    def calculate(self, state: PetState, phase: float) -> AnimationParams:
        if state == PetState.idle:
            return AnimationParams(dx=0.0, dy=math.sin(phase) * 8.0)
        elif state == PetState.thinking:
            return AnimationParams(
                dx=math.sin(phase * 3) * 3.0,
                dy=math.sin(phase * 2) * 5.0,
            )
        elif state == PetState.done:
            raw = math.sin(phase * 3)
            return AnimationParams(dx=0.0, dy=max(0.0, raw) * 40.0)
        elif state == PetState.waiting:
            return AnimationParams(
                dx=math.sin(phase * 0.4) * 2.0,
                dy=math.sin(phase * 0.6) * 5.0,
            )
        return AnimationParams()
