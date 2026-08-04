#!/usr/bin/env python3
"""PermissionRequest フック: Claude Pet に承認リクエストを送り、ボタン操作の結果を返す

Claude Pet が起動していない場合やタイムアウト時は何も出力せず終了し、
通常のターミナル上の許可プロンプトにフォールバックする。
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

TERMINAL_APPS = {"ghostty", "Ghostty", "iTerm2", "Terminal", "Warp", "Hyper", "Alacritty", "WezTerm"}


def _find_terminal_pid() -> int:
    pid = os.getpid()
    while pid > 1:
        try:
            r = subprocess.run(
                ["ps", "-p", str(pid), "-o", "ppid=,comm="],
                capture_output=True, text=True, timeout=2,
            )
            parts = r.stdout.strip().split(None, 1)
            if len(parts) < 2:
                break
            ppid, comm = int(parts[0]), os.path.basename(parts[1].strip())
            if comm in TERMINAL_APPS:
                return pid
            pid = ppid
        except (ValueError, OSError, subprocess.SubprocessError):
            break
    return 0

PORT = 3131
TIMEOUT_SEC = 290
POLL_SEC = 0.5
MAX_DETAIL = 300

DEBUG_LOG = "/tmp/claude-pet-hook.log"


def _log(msg: str) -> None:
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} [{os.getpid()}] {msg}\n")
    except OSError:
        pass


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        data = {}

    tool = data.get("tool_name") or (data.get("tool") or {}).get("name") or "Unknown"
    tool_input = data.get("tool_input") or (data.get("tool") or {}).get("input") or {}
    detail = (
        tool_input.get("command")
        or tool_input.get("file_path")
        or tool_input.get("url")
        or json.dumps(tool_input, ensure_ascii=False)
    )
    detail = str(detail)[:MAX_DETAIL]

    _log(f"request: tool={tool} detail={detail[:60]}")
    request_id = str(uuid.uuid4())
    payload = json.dumps(
        {
            "id": request_id,
            "tool": tool,
            "detail": detail,
            "cwd": os.getcwd(),
            "terminal_pid": _find_terminal_pid(),
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/permission",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=3)
    except (urllib.error.URLError, OSError) as e:
        _log(f"POST failed: {e}")
        return  # Pet が起動していない → 通常のプロンプトへ
    _log(f"POSTed id={request_id}")

    deadline = time.time() + TIMEOUT_SEC
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/permission/{request_id}", timeout=3
            ) as res:
                decision = json.loads(res.read()).get("decision")
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            _log(f"poll failed: {e}")
            return

        if decision:
            _log(f"decision={decision}")
        if decision == "allow":
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PermissionRequest",
                            "decision": {"behavior": "allow"},
                        }
                    }
                )
            )
            return
        if decision == "deny":
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PermissionRequest",
                            "decision": {
                                "behavior": "deny",
                                "message": "Claude Pet で拒否されました",
                            },
                        }
                    }
                )
            )
            return
        time.sleep(POLL_SEC)
    _log("timed out with no decision")
    # タイムアウト → 出力なし = 通常のプロンプトへ


if __name__ == "__main__":
    main()
