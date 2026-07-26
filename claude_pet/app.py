from __future__ import annotations

import subprocess

from AppKit import (
    NSApplication,
    NSBackingStoreBuffered,
    NSColor,
    NSMakeRect,
    NSScreen,
    NSWindowStyleMaskBorderless,
)
from Foundation import NSMakePoint

from claude_pet.constants import PORT
from claude_pet.domain.enums import PetState
from claude_pet.infrastructure.config_repo import ConfigRepo
from claude_pet.infrastructure.http_server import HttpServer
from claude_pet.infrastructure.notification_service import NotificationService
from claude_pet.ui_queue import ui_queue
from claude_pet.usecases.animation_usecase import AnimationUsecase
from claude_pet.usecases.config_usecase import ConfigUsecase
from claude_pet.usecases.log_usecase import LogUsecase
from claude_pet.views.pet_window import PetView, PetWindow, PetWindowDelegate


def main() -> None:
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(1)

    # ── Infrastructure ─────────────────────────────────────────────────────
    config_repo = ConfigRepo()
    http_server = HttpServer()
    notifier = NotificationService()

    # ── Usecases ───────────────────────────────────────────────────────────
    animation_usecase = AnimationUsecase()
    log_usecase = LogUsecase()
    config_usecase = ConfigUsecase(config_repo)

    # ── Screen setup ───────────────────────────────────────────────────────
    screen_frame = NSScreen.mainScreen().frame()
    win_w, win_h = 162, 260
    win_x = screen_frame.size.width - win_w - 20
    win_y = 80

    window = PetWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(win_x, win_y, win_w, win_h),
        NSWindowStyleMaskBorderless,
        NSBackingStoreBuffered,
        False,
    )
    window.setBackgroundColor_(NSColor.clearColor())
    window.setOpaque_(False)
    window.setHasShadow_(False)
    window.setLevel_(25)
    window.setCollectionBehavior_(1 | 4)
    window.setIgnoresMouseEvents_(False)
    window.setMovable_(False)

    delegate = PetWindowDelegate.alloc().init()
    window.setDelegate_(delegate)

    # ── Pet View ───────────────────────────────────────────────────────────
    initial_state = PetState.idle
    initial_text = "起動したよ！"

    pet_view = PetView.alloc().initWithFrame_state_bubbleText_logs_animation_onActivateTerminal_(
        NSMakeRect(0, 0, win_w, win_h),
        initial_state,
        initial_text,
        log_usecase.logs,
        animation_usecase.calculate,
        _activate_terminal,
    )
    window.setContentView_(pet_view)
    window.makeKeyAndOrderFront_(None)

    # ── Log Panel ──────────────────────────────────────────────────────────
    from claude_pet.views.log_panel import create_log_panel

    log_panel = create_log_panel(
        logs=log_usecase.logs,
        get_theme=lambda: config_usecase.load_theme(),
        on_toggle_theme=lambda: _toggle_theme(config_usecase, log_panel),
        on_settings=lambda: _open_settings(config_usecase, pet_view),
        on_session=_activate_terminal,
    )
    pet_view.set_log_panel(log_panel)
    pet_view.set_theme_getter(lambda: config_usecase.load_theme())

    from claude_pet.constants import BUBBLE_Y, PANEL_H, PANEL_W

    def toggle_log_panel() -> None:
        if log_panel.isVisible():
            log_panel.orderOut_(None)
            return
        win = window
        wf = win.frame()
        px = wf.origin.x - PANEL_W - 8
        py = max(10, wf.origin.y + BUBBLE_Y - PANEL_H - 10)
        log_panel.setFrameOrigin_(NSMakePoint(px, py))
        log_panel.makeKeyAndOrderFront_(None)

    pet_view.set_toggle_log_callback(toggle_log_panel)

    # デバッグ用: CLAUDE_PET_SHOW_LOG=1 で起動時にログパネルを表示
    import os

    if os.environ.get("CLAUDE_PET_SHOW_LOG"):
        ui_queue.put(toggle_log_panel)

    # ── Notification handler ───────────────────────────────────────────────
    def on_notify(state: str, message: str | None) -> None:
        notification = notifier.build_notification(state, message)
        notifier.show_osx_notification(notification)

        def update() -> None:
            pet_state = PetState(notification.state)
            pet_view.state = pet_state
            pet_view.show_bubble(notification.message)
            log_entry = log_usecase.add(notification.message)
            pet_view.add_log_entry(log_entry)

        ui_queue.put(update)

    http_server.start(on_notify)
    print(f"Claude Pet 起動完了 (port {PORT})")
    app.run()


def _toggle_theme(config_usecase: ConfigUsecase, log_panel) -> None:
    config_usecase.toggle_theme()
    log_panel.contentView().setNeedsDisplay_(True)


def _open_settings(config_usecase: ConfigUsecase, pet_view: PetView) -> None:
    from claude_pet.views.settings_panel import (
        SETTINGS_H,
        SETTINGS_W,
        create_settings_panel,
    )

    raw_config = config_usecase._repo.load()
    _settings_panel = create_settings_panel(
        raw_config,
        on_image_change=lambda path: _on_image_change(
            config_usecase, pet_view, path, _settings_panel
        ),
    )
    sf = NSScreen.mainScreen().frame()
    sx = (sf.size.width - SETTINGS_W) / 2
    sy = (sf.size.height - SETTINGS_H) / 2
    _settings_panel.setFrameOrigin_(NSMakePoint(sx, sy))
    _settings_panel.makeKeyAndOrderFront_(None)


def _on_image_change(
    config_usecase: ConfigUsecase,
    pet_view: PetView,
    path: str | None,
    panel,
) -> None:
    config_usecase.set_character_image(path)
    pet_view.reload_character_image(path)
    cfg = panel.contentView()._config
    cfg["character_image"] = path


def _activate_terminal() -> None:
    script = """
    tell application "System Events"
        set termApps to {"iTerm2", "Terminal", "Warp", "Hyper", "Alacritty", "WezTerm"}
        repeat with appName in termApps
            if (count of (every process whose name is appName)) > 0 then
                set frontmost of (first process whose name is appName) to true
                return
            end if
        end repeat
    end tell
    """
    subprocess.Popen(["osascript", "-e", script])
