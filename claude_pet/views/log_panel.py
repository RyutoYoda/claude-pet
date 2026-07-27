from __future__ import annotations

from collections.abc import Callable

import objc
from AppKit import (
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSMakeRect,
    NSPanel,
    NSView,
    NSWindowStyleMaskBorderless,
)
from Foundation import NSAttributedString, NSMakePoint, NSPoint

from claude_pet.constants import (
    DETAIL_H,
    LOG_ROW_H,
    LOG_ROWS_VISIBLE,
    PANEL_H,
    PANEL_HEADER_H,
    PANEL_W,
)
from claude_pet.domain.entities import LogEntry
from claude_pet.domain.value_objects import Theme


class LogPanel(NSPanel):
    def canBecomeKeyWindow(self) -> bool:
        return True

    def canBecomeMainWindow(self) -> bool:
        return False


class LogPanelView(NSView):
    def initWithLogs_onTheme_onToggleTheme_onSettings_onSession_(
        self,
        logs_ref: list[LogEntry],
        get_theme: Callable[[], Theme],
        on_toggle_theme: Callable[[], None],
        on_settings: Callable[[], None],
        on_session: Callable[[], None],
    ) -> LogPanelView | None:
        self = objc.super(LogPanelView, self).initWithFrame_(
            NSMakeRect(0, 0, PANEL_W, PANEL_H)
        )
        if self is None:
            return None
        self._logs = logs_ref
        self._get_theme = get_theme
        self._on_toggle_theme = on_toggle_theme
        self._scroll_offset = 0
        self._selected_row: int | None = None
        self._on_settings = on_settings
        self._on_session = on_session
        self._get_voice: Callable[[], bool] | None = None
        self._on_toggle_voice: Callable[[], None] | None = None
        return self

    def set_voice_controls(
        self,
        get_voice: Callable[[], bool],
        on_toggle_voice: Callable[[], None],
    ) -> None:
        self._get_voice = get_voice
        self._on_toggle_voice = on_toggle_voice

    def _theme(self) -> Theme:
        return self._get_theme()

    def _colors(self) -> dict:
        if self._theme().dark_mode:
            return {
                "bg": NSColor.colorWithRed_green_blue_alpha_(0.10, 0.10, 0.10, 0.98),
                "border": NSColor.colorWithRed_green_blue_alpha_(0.45, 0.45, 0.45, 0.6),
                "title": NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0),
                "sep": NSColor.colorWithRed_green_blue_alpha_(0.5, 0.5, 0.5, 0.5),
                "row_text": NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0),
                "row_time": NSColor.colorWithRed_green_blue_alpha_(
                    0.75, 0.75, 0.75, 1.0
                ),
                "row_alt": NSColor.colorWithRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.05),
                "row_sel": NSColor.colorWithRed_green_blue_alpha_(0.3, 0.6, 1.0, 0.25),
                "x_btn": NSColor.colorWithRed_green_blue_alpha_(1.0, 0.45, 0.45, 1.0),
                "scroll": NSColor.colorWithRed_green_blue_alpha_(0.65, 0.65, 0.65, 0.5),
                "theme_btn": NSColor.colorWithRed_green_blue_alpha_(0.9, 0.9, 0.9, 1.0),
                "hint": NSColor.colorWithRed_green_blue_alpha_(0.65, 0.65, 0.65, 1.0),
                "gear_btn": NSColor.colorWithRed_green_blue_alpha_(
                    0.80, 0.80, 0.80, 1.0
                ),
                "session_btn": NSColor.colorWithRed_green_blue_alpha_(
                    0.25, 0.85, 0.4, 1.0
                ),
            }
        else:
            return {
                "bg": NSColor.colorWithWhite_alpha_(0.97, 0.98),
                "border": NSColor.colorWithWhite_alpha_(0.7, 0.8),
                "title": NSColor.colorWithWhite_alpha_(0.15, 1.0),
                "sep": NSColor.colorWithWhite_alpha_(0.75, 1.0),
                "row_text": NSColor.colorWithWhite_alpha_(0.2, 1.0),
                "row_time": NSColor.colorWithWhite_alpha_(0.5, 1.0),
                "row_alt": NSColor.colorWithWhite_alpha_(0.0, 0.04),
                "row_sel": NSColor.colorWithRed_green_blue_alpha_(0.2, 0.5, 0.9, 0.15),
                "x_btn": NSColor.colorWithRed_green_blue_alpha_(0.85, 0.2, 0.2, 1.0),
                "scroll": NSColor.colorWithWhite_alpha_(0.5, 0.5),
                "theme_btn": NSColor.colorWithWhite_alpha_(0.4, 1.0),
                "hint": NSColor.colorWithWhite_alpha_(0.6, 1.0),
                "gear_btn": NSColor.colorWithWhite_alpha_(0.45, 1.0),
                "session_btn": NSColor.colorWithRed_green_blue_alpha_(
                    0.1, 0.6, 0.25, 1.0
                ),
            }

    def drawRect_(self, dirty_rect) -> None:
        c = self._colors()

        c["bg"].set()
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            self.bounds(), 12, 12
        )
        path.fill()

        c["border"].set()
        path.setLineWidth_(1.0)
        path.stroke()

        header_y = PANEL_H - PANEL_HEADER_H

        NSAttributedString.alloc().initWithString_attributes_(
            "作業ログ",
            {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(11),
                NSForegroundColorAttributeName: c["title"],
            },
        ).drawAtPoint_(NSMakePoint(12, header_y + 12))

        NSAttributedString.alloc().initWithString_attributes_(
            "⚙",
            {
                NSFontAttributeName: NSFont.systemFontOfSize_(18),
                NSForegroundColorAttributeName: c["gear_btn"],
            },
        ).drawAtPoint_(NSMakePoint(PANEL_W - 56, header_y + 9))

        if self._get_voice is not None:
            voice_icon = "🔊" if self._get_voice() else "🔇"
            NSAttributedString.alloc().initWithString_attributes_(
                voice_icon,
                {
                    NSFontAttributeName: NSFont.systemFontOfSize_(12),
                    NSForegroundColorAttributeName: c["theme_btn"],
                },
            ).drawAtPoint_(NSMakePoint(PANEL_W - 88, header_y + 12))

        theme_icon = "🌙" if self._theme().dark_mode else "☀️"
        NSAttributedString.alloc().initWithString_attributes_(
            theme_icon,
            {
                NSFontAttributeName: NSFont.systemFontOfSize_(12),
                NSForegroundColorAttributeName: c["theme_btn"],
            },
        ).drawAtPoint_(NSMakePoint(PANEL_W - 26, header_y + 12))

        c["sep"].set()
        sep = NSBezierPath.bezierPath()
        sep.moveToPoint_(NSMakePoint(8, header_y))
        sep.lineToPoint_(NSMakePoint(PANEL_W - 8, header_y))
        sep.setLineWidth_(0.5)
        sep.stroke()

        sep2 = NSBezierPath.bezierPath()
        sep2.moveToPoint_(NSMakePoint(8, DETAIL_H))
        sep2.lineToPoint_(NSMakePoint(PANEL_W - 8, DETAIL_H))
        sep2.setLineWidth_(0.5)
        sep2.stroke()

        if self._selected_row is not None and 0 <= self._selected_row < len(self._logs):
            full_msg = self._logs[self._selected_row].message
            NSAttributedString.alloc().initWithString_attributes_(
                full_msg,
                {
                    NSFontAttributeName: NSFont.systemFontOfSize_(9),
                    NSForegroundColorAttributeName: c["row_text"],
                },
            ).drawInRect_(NSMakeRect(10, 30, PANEL_W - 20, DETAIL_H - 34))

            # セッションに飛ぶボタン（水色）
            NSColor.colorWithRed_green_blue_alpha_(0.35, 0.65, 0.95, 0.95).set()
            btn = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(PANEL_W - 122, 5, 112, 20), 6, 6
            )
            btn.fill()
            NSAttributedString.alloc().initWithString_attributes_(
                "セッションに飛ぶ →",
                {
                    NSFontAttributeName: NSFont.boldSystemFontOfSize_(9),
                    NSForegroundColorAttributeName: NSColor.whiteColor(),
                },
            ).drawAtPoint_(NSMakePoint(PANEL_W - 114, 10))
        else:
            NSAttributedString.alloc().initWithString_attributes_(
                "← 行をクリックで全文表示",
                {
                    NSFontAttributeName: NSFont.systemFontOfSize_(9),
                    NSForegroundColorAttributeName: c["hint"],
                },
            ).drawAtPoint_(NSMakePoint(10, DETAIL_H // 2 - 4))

        row_attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(10),
            NSForegroundColorAttributeName: c["row_text"],
        }
        time_attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(9),
            NSForegroundColorAttributeName: c["row_time"],
        }
        x_btn_attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(9),
            NSForegroundColorAttributeName: c["x_btn"],
        }

        start = self._scroll_offset
        end = min(start + LOG_ROWS_VISIBLE, len(self._logs))

        for i in range(start, end):
            entry = self._logs[i]
            abs_row = i
            rel_row = i - start
            y = header_y - (rel_row + 1) * LOG_ROW_H
            bg_rect = NSMakeRect(4, y, PANEL_W - 8, LOG_ROW_H - 2)

            if abs_row == self._selected_row:
                c["row_sel"].set()
                NSBezierPath.fillRect_(bg_rect)
            elif rel_row % 2 == 0:
                c["row_alt"].set()
                NSBezierPath.fillRect_(bg_rect)

            NSAttributedString.alloc().initWithString_attributes_(
                entry.timestamp, time_attrs
            ).drawAtPoint_(NSMakePoint(10, y + 5))

            truncated = (
                entry.message[:16] + "…" if len(entry.message) > 17 else entry.message
            )
            truncated = truncated.replace("\n", " ")
            NSAttributedString.alloc().initWithString_attributes_(
                truncated, row_attrs
            ).drawAtPoint_(NSMakePoint(42, y + 4))

            NSAttributedString.alloc().initWithString_attributes_(
                "✕", x_btn_attrs
            ).drawAtPoint_(NSMakePoint(PANEL_W - 20, y + 5))

        if len(self._logs) > LOG_ROWS_VISIBLE:
            total = len(self._logs)
            track_h = header_y - DETAIL_H - 8
            thumb_h = max(16, track_h * LOG_ROWS_VISIBLE // total)
            thumb_y = (
                DETAIL_H
                + 4
                + (track_h - thumb_h)
                * self._scroll_offset
                // max(1, total - LOG_ROWS_VISIBLE)
            )
            c["scroll"].set()
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                NSMakeRect(PANEL_W - 5, thumb_y, 3, thumb_h), 1, 1
            ).fill()

    def scrollWheel_(self, event) -> None:
        delta = int(event.scrollingDeltaY())
        max_offset = max(0, len(self._logs) - LOG_ROWS_VISIBLE)
        self._scroll_offset = max(0, min(self._scroll_offset - delta, max_offset))
        self._selected_row = None
        self.setNeedsDisplay_(True)

    def _row_at_point(self, loc: NSPoint) -> int:
        header_y = PANEL_H - PANEL_HEADER_H
        if loc.y >= header_y or loc.y <= DETAIL_H:
            return -1
        row = int((header_y - loc.y) // LOG_ROW_H)
        actual = self._scroll_offset + row
        return actual if actual < len(self._logs) else -1

    def mouseDown_(self, event) -> None:
        pass

    def mouseUp_(self, event) -> None:
        loc = event.locationInWindow()
        header_y = PANEL_H - PANEL_HEADER_H

        if loc.y >= header_y:
            if loc.x >= PANEL_W - 30:
                self._on_toggle_theme()
                self.setNeedsDisplay_(True)
            elif loc.x >= PANEL_W - 60:
                self._on_settings()
            elif loc.x >= PANEL_W - 92 and self._on_toggle_voice is not None:
                self._on_toggle_voice()
                self.setNeedsDisplay_(True)
            return

        if loc.y <= DETAIL_H:
            # 「セッションに飛ぶ」ボタン
            if (
                self._selected_row is not None
                and PANEL_W - 122 <= loc.x <= PANEL_W - 10
                and 5 <= loc.y <= 25
            ):
                self._on_session()
                return
            self._selected_row = None
            self.setNeedsDisplay_(True)
            return

        row = self._row_at_point(loc)
        if row < 0:
            return

        if loc.x >= PANEL_W - 26:
            if row < len(self._logs):
                self._logs.pop(row)
                max_offset = max(0, len(self._logs) - LOG_ROWS_VISIBLE)
                self._scroll_offset = min(self._scroll_offset, max_offset)
                if self._selected_row is not None:
                    if self._selected_row == row:
                        self._selected_row = None
                    elif self._selected_row > row:
                        self._selected_row -= 1
            self.setNeedsDisplay_(True)
        else:
            self._selected_row = None if self._selected_row == row else row
            self.setNeedsDisplay_(True)

    def acceptsFirstMouse_(self, event) -> bool:
        return True


def create_log_panel(
    logs: list[LogEntry],
    get_theme: Callable[[], Theme],
    on_toggle_theme: Callable[[], None],
    on_settings: Callable[[], None],
    on_session: Callable[[], None],
) -> LogPanel:
    panel = LogPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, PANEL_W, PANEL_H),
        NSWindowStyleMaskBorderless,
        NSBackingStoreBuffered,
        False,
    )
    panel.setBackgroundColor_(NSColor.clearColor())
    panel.setOpaque_(False)
    panel.setHasShadow_(True)
    panel.setLevel_(25)
    panel.setCollectionBehavior_(1 | 4)
    panel.setIgnoresMouseEvents_(False)

    view = (
        LogPanelView.alloc().initWithLogs_onTheme_onToggleTheme_onSettings_onSession_(
            logs, get_theme, on_toggle_theme, on_settings, on_session
        )
    )
    panel.setContentView_(view)
    panel.makeFirstResponder_(view)
    return panel
