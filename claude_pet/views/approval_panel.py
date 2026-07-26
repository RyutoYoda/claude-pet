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
from Foundation import NSMakePoint, NSString

APPROVAL_W = 300
APPROVAL_H = 150

_BTN_ALLOW = NSMakeRect(24, 12, 116, 34)
_BTN_DENY = NSMakeRect(160, 12, 116, 34)


class ApprovalPanel(NSPanel):
    def canBecomeKeyWindow(self) -> bool:
        return True

    def canBecomeMainWindow(self) -> bool:
        return False


class ApprovalPanelView(NSView):
    def initWithOnDecide_(
        self, on_decide: Callable[[str], None]
    ) -> ApprovalPanelView | None:
        self = objc.super(ApprovalPanelView, self).initWithFrame_(
            NSMakeRect(0, 0, APPROVAL_W, APPROVAL_H)
        )
        if self is None:
            return None
        self._on_decide = on_decide
        self._tool = ""
        self._detail = ""
        return self

    def set_request(self, tool: str, detail: str) -> None:
        self._tool = tool
        self._detail = detail
        self.setNeedsDisplay_(True)

    def summary(self) -> str:
        return f"{self._tool}: {self._detail}"

    def drawRect_(self, dirty_rect) -> None:
        NSColor.colorWithWhite_alpha_(0.97, 0.98).set()
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            self.bounds(), 12, 12
        )
        path.fill()
        NSColor.colorWithRed_green_blue_alpha_(0.95, 0.6, 0.1, 0.9).set()
        path.setLineWidth_(2.0)
        path.stroke()

        NSString.stringWithString_("🔐 承認リクエスト").drawAtPoint_withAttributes_(
            NSMakePoint(16, APPROVAL_H - 30),
            {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(13),
                NSForegroundColorAttributeName: NSColor.colorWithWhite_alpha_(
                    0.15, 1.0
                ),
            },
        )

        NSString.stringWithString_(self._tool).drawAtPoint_withAttributes_(
            NSMakePoint(16, APPROVAL_H - 52),
            {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(11),
                NSForegroundColorAttributeName: NSColor.colorWithRed_green_blue_alpha_(
                    0.2, 0.4, 0.8, 1.0
                ),
            },
        )

        detail = self._detail
        if len(detail) > 120:
            detail = detail[:119] + "…"
        NSString.stringWithString_(detail).drawInRect_withAttributes_(
            NSMakeRect(16, 54, APPROVAL_W - 32, APPROVAL_H - 110),
            {
                NSFontAttributeName: NSFont.systemFontOfSize_(10),
                NSForegroundColorAttributeName: NSColor.colorWithWhite_alpha_(
                    0.3, 1.0
                ),
            },
        )

        self._draw_btn(
            "✅ 承認",
            _BTN_ALLOW,
            NSColor.colorWithRed_green_blue_alpha_(0.2, 0.7, 0.35, 0.9),
        )
        self._draw_btn(
            "❌ 拒否",
            _BTN_DENY,
            NSColor.colorWithRed_green_blue_alpha_(0.85, 0.3, 0.3, 0.9),
        )

    def _draw_btn(self, label: str, rect, color) -> None:
        color.set()
        btn = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, 8, 8)
        btn.fill()
        NSString.stringWithString_(label).drawAtPoint_withAttributes_(
            NSMakePoint(rect.origin.x + 26, rect.origin.y + 9),
            {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(12),
                NSForegroundColorAttributeName: NSColor.whiteColor(),
            },
        )

    def mouseDown_(self, event) -> None:
        pass

    def mouseUp_(self, event) -> None:
        loc = event.locationInWindow()
        if self._hit(loc, _BTN_ALLOW):
            self._on_decide("allow")
        elif self._hit(loc, _BTN_DENY):
            self._on_decide("deny")

    @staticmethod
    def _hit(loc, rect) -> bool:
        return (
            rect.origin.x <= loc.x <= rect.origin.x + rect.size.width
            and rect.origin.y <= loc.y <= rect.origin.y + rect.size.height
        )

    def acceptsFirstMouse_(self, event) -> bool:
        return True


def create_approval_panel(
    on_decide: Callable[[str], None],
) -> tuple[ApprovalPanel, ApprovalPanelView]:
    panel = ApprovalPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, APPROVAL_W, APPROVAL_H),
        NSWindowStyleMaskBorderless,
        NSBackingStoreBuffered,
        False,
    )
    panel.setBackgroundColor_(NSColor.clearColor())
    panel.setOpaque_(False)
    panel.setHasShadow_(True)
    panel.setLevel_(26)
    panel.setCollectionBehavior_(1 | 4)
    panel.setIgnoresMouseEvents_(False)

    view = ApprovalPanelView.alloc().initWithOnDecide_(on_decide)
    panel.setContentView_(view)
    panel.makeFirstResponder_(view)
    return panel, view
