# Claude Pet

Claude Code の実行状態を可視化する macOS デスクトップペット。

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/macOS-000000?style=flat&logo=apple&logoColor=white" />
  <img src="https://img.shields.io/badge/AppKit_(PyObjC)-2396F3?style=flat&logo=apple&logoColor=white" />
  <img src="https://img.shields.io/badge/Claude_Code-191919?style=flat&logo=anthropic&logoColor=white" />
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=githubactions&logoColor=white" />
</p>

<img width="726" height="455" alt="スクリーンショット 2026-07-27 10 50 53" src="https://github.com/user-attachments/assets/8eefa3ae-1050-4ab3-a691-f8eadcdb1738" />


## 機能

- Claude Code の状態（思考中・完了・待機）をキャラクターのアニメーションで表示
- 吹き出しでメッセージを表示
- 通知を音声で読み上げ（画面を見ていなくても声で作業状況がわかる）
- 許可リクエストをペット上で承認/拒否（ターミナルに切り替えずに承認できる）
- macOS 通知センターに通知
- 作業ログの表示・管理
- ダークモード / ライトモード切替
- キャラクター画像のカスタマイズ
<img width="270" height="305" alt="スクリーンショット 2026-07-27 16 10 23" src="https://github.com/user-attachments/assets/e1247549-48e7-46f7-8d6f-6975e256fae7" />

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

### 起動（重要）

このアプリは **Dock や Launchpad に表示されません**（デスクトップに常駐するタイプのアプリのため）。
インストールしただけでは何も起きません。**ターミナルから以下のコマンドで起動してください：**

```bash
open /Applications/Claude\ Pet.app
```

数秒後、画面右下にキャラクターが表示されます。
初回起動時のみ、依存ライブラリの自動インストールに少し時間がかかります（要インターネット接続・Python 3.10 以上）。

### 停止

Dock にアイコンがないため、終了もターミナルから行います：

```bash
pkill -f claude_pet
```

### アップデート（新しいバージョンを入れるとき）

1. まず動作中のアプリを停止：
   ```bash
   pkill -f claude_pet
   ```
2. 新しい PKG をインストール（上書きされます）
3. 再起動：
   ```bash
   open /Applications/Claude\ Pet.app
   ```

**アプリを停止せずに PKG を入れ直すと、古いバージョンが動き続けたままになるので注意してください。**

### アンインストール（完全削除）

```bash
# 1. アプリを停止
pkill -f claude_pet

# 2. アプリ本体を削除
sudo rm -rf "/Applications/Claude Pet.app"

# 3. 依存ライブラリを削除
rm -rf ~/.local/share/claude-pet

# 4. 設定ファイルを削除
rm -f ~/Library/Preferences/claude-pet.json
```

最後に、`~/.claude/settings.json` に連携フックを追加していた場合はその記述も削除してください。

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
    ],
    "PermissionRequest": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 '/Applications/Claude Pet.app/Contents/Resources/permission_hook.py'",
            "timeout": 330
          }
        ]
      }
    ]
  }
}
```

**各フックの役割:**

| フック | 動作 |
|--------|------|
| `Stop` | Claude Code の応答完了時に、メッセージを吹き出し＋音声＋作業ログでお知らせ |
| `Notification` | Claude Code が入力待ちになったときにお知らせ |
| `PermissionRequest` | 許可リクエストをペット上の承認パネルに表示 |

### 承認機能（PermissionRequest フック）

Claude Code がコマンド実行などの許可を求めると、ペットの横に承認リクエストパネルが表示されます。

- 「承認 / 拒否」をクリックするだけで回答完了。ターミナルに戻る必要はありません（別の画面を見ながらでも承認できます）
- 承認リクエストが来ると音声でも「◯◯の承認をお願いします」とお知らせします
- 承認/拒否の結果は作業ログにも記録されます
- **フォールバック**: ペットが起動していないとき・約5分間ボタンを押さなかったときは、通常のターミナル上のプロンプトに自動で戻ります
- 注意: ペットのパネルとターミナルのプロンプトが同時に出ている場合、先に操作した方が優先されます

### 音声読み上げ

通知が来るとペットがメッセージを読み上げます（macOS 内蔵の音声合成を使用）。

- 通知メッセージを最大80文字まで読み上げ
- 連続で通知が来たときは前の読み上げを止めてから喋ります（重なりません）
- ひとりごと（「ひまだな〜」など）は喋りません — 通知のときだけ
- **オン/オフ切替**: ログパネルのヘッダーにある **🔊/🔇** アイコンをクリック（設定は保存されます）
- デフォルトは **ON** です

### 操作

| 操作 | 動作 |
|------|------|
| キャラクターをドラッグ | ウィンドウ移動 |
| キャラクター上部をクリック | ターミナルを前面化 |
| キャラクター下部をクリック | ログパネル表示/非表示 |
| ログ行をクリック | メッセージ全文表示 |
| ✕ ボタン | ログ削除 |
| 「セッションに飛ぶ」ボタン | 全文表示エリアからターミナルを前面化 |
| 🔊/🔇 ボタン | 音声読み上げのオン/オフ |
| 🌙/☀️ ボタン | テーマ切替 |
| ⚙ ボタン | 設定パネル |
| 承認パネルの ✅/❌ | 許可リクエストに回答 |

## ライセンス

[MIT](LICENSE)
