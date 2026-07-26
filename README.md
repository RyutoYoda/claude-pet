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

### 方法 1: pip インストール

```bash
pip install claude-pet
```

### 方法 2: GitHub Releases からダウンロード

[Releases](https://github.com/RyutoYoda/claude-pet/releases) から最新の `.pkg` をダウンロードしてインストール。

### 方法 3: ソースから実行

```bash
git clone https://github.com/RyutoYoda/claude-pet.git
cd claude-pet
uv run python -m claude_pet
```

## 使い方

### 起動

```bash
claude-pet
```

または

```bash
uv run python -m claude_pet
```

### Claude Code との連携

Claude Code の `~/.claude/settings.jsonl` にフックを設定:

```json
{
  "OnHook": "python /path/to/notify_hook.py"
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

## アーキテクチャ

Clean Architecture に従って構成:

```
claude_pet/
├── domain/          # エンティティ、値オブジェクト、Enum
│   ├── entities.py       # LogEntry, Notification
│   ├── enums.py          # PetState
│   └── value_objects.py  # AnimationParams, Theme
├── usecases/        # アプリケーション固有のビジネスロジック
│   ├── animation_usecase.py
│   ├── config_usecase.py
│   └── log_usecase.py
├── infrastructure/  # 外部サービス（HTTP, ファイル, 通知）
│   ├── config_repo.py
│   ├── http_server.py
│   └── notification_service.py
├── views/           # PyObjC UI レイヤー
│   ├── pet_window.py
│   ├── log_panel.py
│   └── settings_panel.py
├── app.py           # Composition Root
└── constants.py
```

## ライセンス

[MIT](LICENSE)
