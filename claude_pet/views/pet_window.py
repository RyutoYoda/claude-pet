from __future__ import annotations

import math
import queue as _queue
import random
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import objc
from AppKit import (
    NSApplication,
    NSBezierPath,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSImage,
    NSImageView,
    NSMakeRect,
    NSObject,
    NSTimer,
    NSView,
    NSWindow,
)
from Foundation import NSMakePoint, NSPoint, NSString

from claude_pet.constants import ASSETS_DIR, BUBBLE_Y, MESSAGES, PANEL_H, PANEL_W
from claude_pet.domain.entities import LogEntry
from claude_pet.domain.enums import PetState
from claude_pet.domain.value_objects import AnimationParams
from claude_pet.ui_queue import ui_queue

if TYPE_CHECKING:
    from AppKit import NSPanel


class PetWindow(NSWindow):
    def canBecomeKeyWindow(self) -> bool:
        return True

    def canBecomeMainWindow(self) -> bool:
        return False


class PetWindowDelegate(NSObject):
    def windowShouldClose_(self, sender) -> bool:
        NSApplication.sharedApplication().terminate_(None)
        return True

    def set_on_screens_changed(self, cb: Callable[[], None]) -> None:
        self._on_screens_changed = cb

    def screensChanged_(self, notification) -> None:
        if hasattr(self, "_on_screens_changed"):
            self._on_screens_changed()


class PetView(NSView):
    def initWithFrame_state_bubbleText_logs_animation_onActivateTerminal_(
        self,
        frame,
        initial_state: PetState,
        initial_text: str,
        logs_ref: list[LogEntry],
        animation_cb: Callable[[PetState, float], AnimationParams],
        on_activate_terminal: Callable[[], None],
    ) -> PetView | None:
        self = objc.super(PetView, self).initWithFrame_(frame)
        if self is None:
            return None

        self._state = initial_state
        self._bubble_text: str = initial_text
        self._logs = logs_ref
        self._animate = animation_cb
        self._on_activate_terminal = on_activate_terminal

        self._bob_phase = 0.0
        self._drag_start: NSPoint | None = None
        self._win_start: NSPoint | None = None
        self._log_panel: NSPanel | None = None
        self._settings_panel: NSPanel | None = None
        self._char_x = 5.0
        self._char_y = 5.0

        self._image_view = NSImageView.alloc().initWithFrame_(
            NSMakeRect(5, 5, 150, 175)
        )
        self._image_view.setImageScaling_(3)
        self._load_character_image()
        self.addSubview_(self._image_view)

        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0 / 60, self, "tick:", None, True
        )
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            20.0, self, "idleTalk:", None, True
        )

        import os

        from claude_pet.constants import BREAK_INTERVAL_MIN

        try:
            break_min = float(os.environ.get("CLAUDE_PET_BREAK_MIN", BREAK_INTERVAL_MIN))
        except ValueError:
            break_min = BREAK_INTERVAL_MIN
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            break_min * 60.0, self, "breakTime:", None, True
        )

        return self

    def set_break_callback(self, cb: Callable[[str], None]) -> None:
        self._on_break = cb

    def set_log_panel(self, panel: NSPanel | None) -> None:
        self._log_panel = panel

    def set_settings_panel(self, panel: NSPanel | None) -> None:
        self._settings_panel = panel

    def set_toggle_log_callback(self, cb: Callable[[], None]) -> None:
        self._toggle_log = cb

    def set_theme_getter(self, getter: Callable) -> None:
        self._get_theme = getter

    def _load_character_image(self, path: str | None = None) -> None:
        if path and Path(path).exists():
            img = NSImage.alloc().initWithContentsOfFile_(path)
        else:
            img = NSImage.alloc().initWithContentsOfFile_(str(ASSETS_DIR / "pet.png"))
        self._image_view.setImage_(img)

    def reload_character_image(self, path: str | None) -> None:
        self._load_character_image(path)

    @property
    def state(self) -> PetState:
        return self._state

    @state.setter
    def state(self, value: PetState) -> None:
        self._state = value
        self._bob_phase = 0.0

    def show_bubble(self, text: str) -> None:
        self._bubble_text = text
        self.setNeedsDisplay_(True)

    def add_log_entry(self, entry: LogEntry) -> None:
        if self._log_panel and self._log_panel.isVisible():
            self._log_panel.contentView().setNeedsDisplay_(True)

    def tick_(self, timer) -> None:
        while not ui_queue.empty():
            try:
                fn = ui_queue.get_nowait()
                fn()
            except _queue.Empty:
                break
        self._bob_phase += 0.05
        params = self._animate(self._state, self._bob_phase)
        self._char_x = 5.0 + params.dx
        self._char_y = 5.0 + params.dy
        self._image_view.setFrame_(NSMakeRect(self._char_x, self._char_y, 150, 175))
        if self._state == PetState.done and self._bob_phase > math.pi:
            self._state = PetState.idle
            self._bob_phase = 0.0
        self.setNeedsDisplay_(True)

    def idleTalk_(self, timer) -> None:
        if self._state == PetState.idle and random.random() < 0.4:
            self.show_bubble(random.choice(MESSAGES["idle"]))

    def breakTime_(self, timer) -> None:
        msg = random.choice(MESSAGES["break"])
        self.show_bubble(msg)
        if hasattr(self, "_on_break"):
            self._on_break(msg)

    def drawRect_(self, dirty_rect) -> None:
        NSColor.clearColor().set()
        NSBezierPath.fillRect_(self.bounds())
        if self._bubble_text:
            self._draw_bubble()

    _CHARS_PER_LINE = 14  # 幅142px・フォント10ptに日本語が収まる目安
    _MAX_LINES = 8

    def _draw_bubble(self) -> None:
        text = self._bubble_text
        max_chars = self._MAX_LINES * self._CHARS_PER_LINE
        if len(text) > max_chars:
            text = text[: max_chars - 1] + "…"
        lines = sum(
            max(1, -(-len(seg) // self._CHARS_PER_LINE))
            for seg in text.split("\n")
        )
        n_lines = min(self._MAX_LINES, lines)
        bh = 20 + n_lines * 16
        bubble_y = 208
        rect = NSMakeRect(2, bubble_y, 156, bh)
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, 8, 8)

        dark = hasattr(self, "_get_theme") and self._get_theme().dark_mode
        if dark:
            NSColor.colorWithWhite_alpha_(0.18, 0.95).set()
            border_color = NSColor.colorWithWhite_alpha_(0.45, 1.0)
            text_color = NSColor.colorWithWhite_alpha_(0.92, 1.0)
        else:
            NSColor.colorWithWhite_alpha_(1.0, 0.95).set()
            border_color = NSColor.colorWithWhite_alpha_(0.35, 1.0)
            text_color = NSColor.colorWithWhite_alpha_(0.15, 1.0)

        path.fill()
        border_color.set()
        path.setLineWidth_(1.0)
        path.stroke()

        NSString.stringWithString_(text).drawInRect_withAttributes_(
            NSMakeRect(8, bubble_y + 6, 142, bh - 10),
            {
                NSFontAttributeName: NSFont.systemFontOfSize_weight_(10, 0.3),
                NSForegroundColorAttributeName: text_color,
            },
        )

    def mouseDown_(self, event) -> None:
        self._drag_start = event.locationInWindow()
        win = self.window()
        if win:
            self._win_start = win.frame().origin

    def mouseDragged_(self, event) -> None:
        if self._drag_start is None or self._win_start is None:
            return
        loc = event.locationInWindow()
        dx = loc.x - self._drag_start.x
        dy = loc.y - self._drag_start.y
        win = self.window()
        if win:
            win.setFrameOrigin_(
                NSMakePoint(self._win_start.x + dx, self._win_start.y + dy)
            )
            if self._log_panel and self._log_panel.isVisible():
                wf = win.frame()
                px, py = self._log_panel_origin(wf)
                self._log_panel.setFrameOrigin_(NSMakePoint(px, py))

    def mouseUp_(self, event) -> None:
        loc = event.locationInWindow()
        if self._drag_start:
            dx = abs(loc.x - self._drag_start.x)
            dy = abs(loc.y - self._drag_start.y)
            if dx < 5 and dy < 5:
                if loc.y >= 205:
                    self._on_activate_terminal()
                else:
                    if hasattr(self, "_toggle_log"):
                        self._toggle_log()
        self._drag_start = None
        self._win_start = None

    def _log_panel_origin(self, wf) -> tuple[float, float]:
        px = wf.origin.x - PANEL_W - 8
        py = max(10, wf.origin.y + BUBBLE_Y - PANEL_H - 10)
        return px, py

    def acceptsFirstMouse_(self, event) -> bool:
        return True
