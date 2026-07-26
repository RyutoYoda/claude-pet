#!/usr/bin/env python3
"""PermissionRequest フック: Claude Pet に承認リクエストを送り、ボタン操作の結果を返す

Claude Pet が起動していない場合やタイムアウト時は何も出力せず終了し、
通常のターミナル上の許可プロンプトにフォールバックする。
"""

import json
import sys
import time
import urllib.error
import urllib.request
import uuid

PORT = 3131
TIMEOUT_SEC = 290
POLL_SEC = 0.5
MAX_DETAIL = 300


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

    request_id = str(uuid.uuid4())
    payload = json.dumps(
        {"id": request_id, "tool": tool, "detail": detail}
    ).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/permission",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=3)
    except (urllib.error.URLError, OSError):
        return  # Pet が起動していない → 通常のプロンプトへ

    deadline = time.time() + TIMEOUT_SEC
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/permission/{request_id}", timeout=3
            ) as res:
                decision = json.loads(res.read()).get("decision")
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            return

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
    # タイムアウト → 出力なし = 通常のプロンプトへ


if __name__ == "__main__":
    main()
