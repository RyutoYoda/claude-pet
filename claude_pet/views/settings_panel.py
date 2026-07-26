from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import objc
from AppKit import (
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSFont,
    NSImage,
    NSImageView,
    NSMakeRect,
    NSOpenPanel,
    NSPanel,
    NSView,
    NSWindowStyleMaskBorderless,
)
from Foundation import NSMakePoint, NSString

from claude_pet.constants import ASSETS_DIR

SETTINGS_W = 280
SETTINGS_H = 320


class SettingsPanel(NSPanel):
    def canBecomeKeyWindow(self) -> bool:
        return True

    def canBecomeMainWindow(self) -> bool:
        return False


class SettingsPanelView(NSView):
    def initWithConfig_onImageChange_(
        self,
        current_config: dict,
        on_image_change: Callable[[str | None], None],
    ) -> SettingsPanelView | None:
        self = objc.super(SettingsPanelView, self).initWithFrame_(
            NSMakeRect(0, 0, SETTINGS_W, SETTINGS_H)
        )
        if self is None:
            return None
        self._config = dict(current_config)
        self._on_image_change = on_image_change
        self._preview: NSImageView = NSImageView.alloc().initWithFrame_(
            NSMakeRect(65, 140, 150, 150)
        )
        self._preview.setImageScaling_(3)
        self._refresh_preview()
        self.addSubview_(self._preview)
        return self

    def _refresh_preview(self) -> None:
        img_path = self._config.get("character_image")
        if img_path and Path(str(img_path)).exists():
            img = NSImage.alloc().initWithContentsOfFile_(str(img_path))
        else:
            img = NSImage.alloc().initWithContentsOfFile_(str(ASSETS_DIR / "pet.png"))
        self._preview.setImage_(img)

    def drawRect_(self, dirty_rect) -> None:
        NSColor.colorWithWhite_alpha_(0.15, 0.96).set()
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            self.bounds(), 12, 12
        )
        path.fill()
        NSColor.colorWithWhite_alpha_(0.4, 0.6).set()
        path.setLineWidth_(1.0)
        path.stroke()

        white = NSColor.colorWithWhite_alpha_(0.9, 1.0)
        gray = NSColor.colorWithWhite_alpha_(0.55, 1.0)

        NSString.stringWithString_("設定").drawAtPoint_withAttributes_(
            NSMakePoint(SETTINGS_W / 2 - 14, SETTINGS_H - 38),
            {"NSFont": NSFont.boldSystemFontOfSize_(14), "NSForegroundColor": white},
        )

        NSString.stringWithString_("キャラクター画像").drawAtPoint_withAttributes_(
            NSMakePoint(12, 128),
            {"NSFont": NSFont.systemFontOfSize_(10), "NSForegroundColor": gray},
        )

        img_path = self._config.get("character_image")
        filename = Path(str(img_path)).name if img_path else "デフォルト"
        NSString.stringWithString_(filename[:34]).drawAtPoint_withAttributes_(
            NSMakePoint(12, 110),
            {
                "NSFont": NSFont.systemFontOfSize_(9),
                "NSForegroundColor": NSColor.colorWithWhite_alpha_(0.7, 1.0),
            },
        )

        self._draw_btn("画像を選択…", NSMakeRect(20, 72, 110, 28))
        self._draw_btn("デフォルトに戻す", NSMakeRect(143, 72, 117, 28))
        self._draw_btn("閉じる", NSMakeRect(80, 24, 120, 32), accent=True)

    def _draw_btn(self, label: str, rect, *, accent: bool = False) -> None:
        if accent:
            NSColor.colorWithRed_green_blue_alpha_(0.3, 0.55, 0.9, 0.85).set()
        else:
            NSColor.colorWithWhite_alpha_(0.3, 0.8).set()
        btn = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, 6, 6)
        btn.fill()
        NSColor.colorWithWhite_alpha_(0.5, 0.5).set()
        btn.setLineWidth_(0.5)
        btn.stroke()
        NSString.stringWithString_(label).drawAtPoint_withAttributes_(
            NSMakePoint(rect.origin.x + 8, rect.origin.y + 8),
            {
                "NSFont": NSFont.systemFontOfSize_(10),
                "NSForegroundColor": NSColor.colorWithWhite_alpha_(0.9, 1.0),
            },
        )

    def mouseDown_(self, event) -> None:
        pass

    def mouseUp_(self, event) -> None:
        x, y = event.locationInWindow().x, event.locationInWindow().y
        if 20 <= x <= 130 and 72 <= y <= 100:
            self._pick_image()
        elif 143 <= x <= 260 and 72 <= y <= 100:
            self._reset_image()
        elif 80 <= x <= 200 and 24 <= y <= 56:
            self.window().orderOut_(None)

    def _pick_image(self) -> None:
        panel = NSOpenPanel.openPanel()
        panel.setTitle_("キャラクター画像を選択")
        panel.setAllowsMultipleSelection_(False)
        panel.setCanChooseDirectories_(False)
        panel.setCanChooseFiles_(True)
        panel.setAllowedFileTypes_(["png", "PNG"])
        if panel.runModal() == 1:
            path = str(panel.URL().path())
            self._config["character_image"] = path
            self._on_image_change(path)
            self._refresh_preview()
            self.setNeedsDisplay_(True)

    def _reset_image(self) -> None:
        self._config["character_image"] = None
        self._on_image_change(None)
        self._refresh_preview()
        self.setNeedsDisplay_(True)

    def acceptsFirstMouse_(self, event) -> bool:
        return True


def create_settings_panel(
    current_config: dict,
    on_image_change: Callable[[str | None], None],
) -> SettingsPanel:
    panel = SettingsPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, SETTINGS_W, SETTINGS_H),
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

    view = SettingsPanelView.alloc().initWithConfig_onImageChange_(
        current_config, on_image_change
    )
    panel.setContentView_(view)
    panel.makeFirstResponder_(view)
    return panel
