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
    # 高さは吹き出しの最大サイズ（8行）が収まるように確保
    win_w, win_h = 162, 360

    def _default_origin() -> tuple[float, float]:
        # visibleFrame は Dock やメニューバーを除いた領域。原点も考慮する
        vf = NSScreen.mainScreen().visibleFrame()
        return (vf.origin.x + vf.size.width - win_w - 20, vf.origin.y + 80)

    win_x, win_y = _default_origin()

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

    # ── ディスプレイ構成変更への追従 ─────────────────────────────────────
    # 外部ディスプレイの接続/切断でウィンドウが画面外に取り残されたら、
    # メイン画面の右下に戻す
    from Foundation import NSIntersectsRect, NSNotificationCenter

    def _ensure_on_screen() -> None:
        wf = window.frame()
        for screen in NSScreen.screens():
            if NSIntersectsRect(wf, screen.frame()):
                return
        x, y = _default_origin()
        window.setFrameOrigin_(NSMakePoint(x, y))
        window.orderFront_(None)

    delegate.set_on_screens_changed(lambda: ui_queue.put(_ensure_on_screen))
    NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
        delegate,
        "screensChanged:",
        "NSApplicationDidChangeScreenParametersNotification",
        None,
    )

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

    def _on_break(msg: str) -> None:
        if config_usecase.voice_enabled():
            notifier.speak(msg)

    pet_view.set_break_callback(_on_break)
    log_panel.contentView().set_voice_controls(
        lambda: config_usecase.voice_enabled(),
        lambda: config_usecase.toggle_voice(),
    )

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
        # 通知センターへの投稿は行わない（osascript 経由だと別アプリ名義の
        # 通知になってしまうため。コード署名対応後にアプリ名義で復活予定）

        def update() -> None:
            if config_usecase.voice_enabled():
                notifier.speak(notification.message)
            pet_state = PetState(notification.state)
            pet_view.state = pet_state
            pet_view.show_bubble(notification.message)
            log_entry = log_usecase.add(notification.message)
            pet_view.add_log_entry(log_entry)

        ui_queue.put(update)

    # ── Permission approval ────────────────────────────────────────────────
    from claude_pet.views.approval_panel import (
        APPROVAL_H,
        APPROVAL_W,
        create_approval_panel,
    )

    pending_requests: list[tuple[str, str, str]] = []
    current_request: dict = {"id": None}

    def _show_next_request() -> None:
        if not pending_requests:
            approval_panel.orderOut_(None)
            current_request["id"] = None
            return
        request_id, tool, detail = pending_requests.pop(0)
        current_request["id"] = request_id
        approval_view.set_request(tool, detail)
        wf = window.frame()
        px = wf.origin.x - APPROVAL_W - 8
        py = wf.origin.y + BUBBLE_Y + 40
        approval_panel.setFrameOrigin_(NSMakePoint(px, py))
        approval_panel.makeKeyAndOrderFront_(None)

    def on_decide(action: str) -> None:
        request_id = current_request["id"]
        if request_id:
            http_server.resolve_permission(request_id, action)
            label = "✅ 承認" if action == "allow" else "❌ 拒否"
            entry = log_usecase.add(f"{label} {approval_view.summary()}")
            pet_view.add_log_entry(entry)
        _show_next_request()

    approval_panel, approval_view = create_approval_panel(on_decide)

    def on_permission(request_id: str, tool: str, detail: str) -> None:
        def update() -> None:
            pending_requests.append((request_id, tool, detail))
            if current_request["id"] is None:
                _show_next_request()
            pet_view.state = PetState.waiting
            pet_view.show_bubble(f"承認お願い！\n{tool}")
            if config_usecase.voice_enabled():
                notifier.speak("Claude Codeからの承認をお願いします！")

        ui_queue.put(update)

    # フックのポーリングが止まったリクエスト（ターミナル側で回答済み・
    # タイムアウト等）はパネルから自動で消す
    import threading
    import time as _time

    _STALE_SEC = 3.0

    def _watch_stale_requests() -> None:
        while True:
            _time.sleep(1.0)

            def check() -> None:
                now = _time.time()
                pending_requests[:] = [
                    r
                    for r in pending_requests
                    if now - http_server.last_poll_at(r[0]) < _STALE_SEC
                ]
                request_id = current_request["id"]
                if (
                    request_id
                    and now - http_server.last_poll_at(request_id) >= _STALE_SEC
                ):
                    entry = log_usecase.add(
                        "承認リクエスト終了（ターミナル側で回答または期限切れ）"
                    )
                    pet_view.add_log_entry(entry)
                    _show_next_request()

            ui_queue.put(check)

    threading.Thread(target=_watch_stale_requests, daemon=True).start()

    http_server.start(on_notify, on_permission)
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
        set termApps to {"ghostty", "Ghostty", "iTerm2", "Terminal", "Warp", "Hyper", "Alacritty", "WezTerm"}
        repeat with appName in termApps
            if (count of (every process whose name is appName)) > 0 then
                set frontmost of (first process whose name is appName) to true
                return
            end if
        end repeat
    end tell
    """
    subprocess.Popen(["osascript", "-e", script])
