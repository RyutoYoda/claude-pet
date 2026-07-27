from pathlib import Path

PORT = 3131

# assets/ は package の親ディレクトリ（プロジェクトルート）に置く
ASSETS_DIR = Path(__file__).parent.parent / "assets"

PANEL_W = 260
PANEL_H = 250
LOG_ROW_H = 24
LOG_ROWS_VISIBLE = 5
PANEL_HEADER_H = 36
DETAIL_H = 62

# ペット窓内での吹き出し下辺 Y（AppKit 座標系 = 下が0）
BUBBLE_Y = 208

MESSAGES: dict[str, list[str]] = {
    "done": ["完了！✨", "お疲れ様！🎉", "やったね！", "できた！💪"],
    "thinking": ["考え中…", "うーん…", "処理中…", "ちょっと待ってね"],
    "waiting": ["確認して！", "呼んだ？", "ここにいるよ！"],
    "idle": ["ひまだな〜", "なにかある？", "ぼーっとしてた…"],
    "break": [
        "そろそろ休憩しようか☕",
        "25分経ったよ！ちょっと休も〜",
        "休憩の時間だよ。伸びでもしよ！",
        "目を休めよう。遠くを見て〜",
    ],
}

# 休憩リマインダーの間隔（分）。環境変数 CLAUDE_PET_BREAK_MIN で上書き可
BREAK_INTERVAL_MIN = 25.0
