# Claude Pet

Claude Code の実行状態を可視化する macOS デスクトップペット。

![screenshot](assets/screenshot.png)

## 機能

- Claude Code の状態（思考中・完了・待機）をキャラクターのアニメーションで表示
- 吹き出しでメッセージを表示
- macOS 通知センターに通知
- 作業ログの表示・管理
- ダークモード / ライトモード切替
- キャラクター画像のカスタマイズ

## インストール

### 推奨: GitHub Releases からダウンロード

[Releases](https://github.com/RyutoYoda/claude-pet/releases) から
`Claude-Pet-*-installer.pkg` をダウンロードして開くだけで使えます。
依存ライブラリの事前インストールは不要です。

> **⚠️ macOS のセキュリティ警告について**
>
> 署名なし配布のため、ダウンロード後に開こうとすると
> 「開発元を確認できないため開けません」と表示される場合があります。
>
> **回避方法（いずれか）:**
> - PKG ファイルを **右クリック → 開く** → 「開く」をクリック
> - または: **システム設定 → プライバシーとセキュリティ** を開き、画面下部の「このまま開く」をクリック

### ソースから実行

```bash
git clone https://github.com/RyutoYoda/claude-pet.git
cd claude-pet
uv run python -m claude_pet
```

## 使い方

### 起動

```bash
open /Applications/Claude\ Pet.app
```

### Claude Code との連携

`~/.claude/settings.json` の `hooks` セクションに以下を追加:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 '/Applications/Claude Pet.app/Contents/Resources/notify_hook.py'"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 '/Applications/Claude Pet.app/Contents/Resources/notify_hook.py'"
          }
        ]
      }
    ]
  }
}
```

### 操作

| 操作 | 動作 |
|------|------|
| キャラクターをドラッグ | ウィンドウ移動 |
| キャラクター上部をクリック | ターミナルを前面化 |
| キャラクター下部をクリック | ログパネル表示/非表示 |
| ログ行をクリック | メッセージ全文表示 |
| ✕ ボタン | ログ削除 |
| ▶ ボタン | ターミナルジャンプ |
| 🌙/☀️ ボタン | テーマ切替 |
| ⚙ ボタン | 設定パネル |

## ライセンス

[MIT](LICENSE)
