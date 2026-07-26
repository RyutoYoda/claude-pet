#!/usr/bin/env python3
"""Stop/Notification フック: 最後のアシスタントメッセージをペットに送る"""

import json
import subprocess
import sys

PORT = 3131
MAX_CHARS = 120


def get_last_assistant_text(transcript_path: str) -> str:
    try:
        with open(transcript_path) as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        for line in reversed(lines):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            content = entry.get("message", {}).get("content", "")
            if isinstance(content, list):
                texts = [
                    b["text"]
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                content = "\n".join(texts)
            if isinstance(content, str):
                content = content.strip()
                if content:
                    return content
    except OSError:
        pass
    return ""


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        data = {}

    transcript_path: str = data.get("transcript_path", "")
    state: str = data.get("hook_type", "stop")
    if state == "stop":
        state = "done"

    text = ""
    if transcript_path:
        text = get_last_assistant_text(transcript_path)

    if not text:
        text = "作業完了！" if state == "done" else "確認してください！"

    if len(text) > MAX_CHARS:
        text = text[: MAX_CHARS - 1] + "…"

    payload = json.dumps({"state": state, "message": text}, ensure_ascii=False)
    subprocess.run(
        [
            "curl",
            "-s",
            "-X",
            "POST",
            f"http://127.0.0.1:{PORT}/notify",
            "-H",
            "Content-Type: application/json",
            "-d",
            payload,
        ],
        capture_output=True,
        timeout=5,
    )


if __name__ == "__main__":
    main()
