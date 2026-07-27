from __future__ import annotations

import random
import subprocess

from AppKit import NSSpeechSynthesizer

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
        # インプロセスの音声合成（say コマンドよりも起動が速い）
        self._synth = NSSpeechSynthesizer.alloc().init()

    def build_notification(self, state: str, message: str | None) -> Notification:
        msg = message or random.choice(
            _DEFAULT_MESSAGES.get(state, _DEFAULT_MESSAGES["idle"])
        )
        return Notification(state=state, message=msg)

    def speak(self, text: str) -> None:
        text = text.replace("\n", "。")[: self._MAX_SPEECH_CHARS]
        if not text.strip():
            return
        # 前の読み上げが残っていたら止める（重なり防止）
        if self._synth.isSpeaking():
            self._synth.stopSpeaking()
        self._synth.startSpeakingString_(text)

    def show_osx_notification(self, notification: Notification) -> None:
        sound = "Glass" if notification.state == "done" else "Ping"
        # AppleScript 文字列として安全になるようエスケープ
        msg = (
            notification.message.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", " ")
        )
        cmd = (
            f'display notification "{msg}" '
            f'with title "Claude Pet" '
            f'subtitle "{notification.state}" '
            f'sound name "{sound}"'
        )
        subprocess.Popen(["osascript", "-e", cmd])
