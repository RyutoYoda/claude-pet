from __future__ import annotations

import random
import subprocess

from claude_pet.domain.entities import Notification

_DEFAULT_MESSAGES: dict[str, list[str]] = {
    "done": ["完了！✨", "お疲れ様！🎉", "やったね！", "できた！💪"],
    "thinking": ["考え中…", "うーん…", "処理中…", "ちょっと待ってね"],
    "waiting": ["確認して！", "呼んだ？", "ここにいるよ！"],
    "idle": ["ひまだな〜", "なにかある？", "ぼーっとしてた…"],
}


class NotificationService:
    _MAX_SPEECH_CHARS = 80

    def __init__(self) -> None:
        self._say_process: subprocess.Popen | None = None

    def build_notification(self, state: str, message: str | None) -> Notification:
        msg = message or random.choice(
            _DEFAULT_MESSAGES.get(state, _DEFAULT_MESSAGES["idle"])
        )
        return Notification(state=state, message=msg)

    def speak(self, text: str) -> None:
        # 前の読み上げが残っていたら止める（重なり防止）
        if self._say_process and self._say_process.poll() is None:
            self._say_process.terminate()
        text = text.replace("\n", "。")[: self._MAX_SPEECH_CHARS]
        if not text.strip():
            return
        self._say_process = subprocess.Popen(["say", text])

    def show_osx_notification(self, notification: Notification) -> None:
        sound = "Glass" if notification.state == "done" else "Ping"
        cmd = (
            f'display notification "{notification.message}" '
            f'title "Claude Pet" '
            f'subtitle "{notification.state}" '
            f'sound name "{sound}"'
        )
        subprocess.Popen(["osascript", "-e", cmd])
