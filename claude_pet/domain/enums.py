from __future__ import annotations

from enum import Enum


class PetState(str, Enum):
    idle = "idle"
    thinking = "thinking"
    done = "done"
    waiting = "waiting"
