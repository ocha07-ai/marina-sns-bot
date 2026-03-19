# マリナ SNS自動投稿ツール

占い師マリナのSNS自動投稿ツール。Claude APIでコンテンツを生成し、X・Threads・TikTokへ自動投稿します。

## セットアップ

### 1. Pythonライブラリをインストール
```
pip install -r requirements.txt
```

### 2. APIキーを設定
`.env.example` を `.env` にコピーして、APIキーを入力してください。
```
copy .env.example .env
```

### 3. テスト実行（投稿しない）
```
scripts\test_post.bat をダブルクリック
```

### 4. 自動投稿を有効化
```
scripts\setup_scheduler.bat を右クリック→管理者として実行
```

## ファイル構成
```
marina-sns-bot/
├── config/
│   ├── settings.yaml   ← 設定変更はここだけ
│   └── prompts.yaml    ← Claudeへの指示
├── src/
│   ├── main.py         ← メイン処理
│   ├── generator.py    ← コンテンツ生成
│   ├── poster_x.py     ← X投稿
│   └── logger.py       ← ログ記録
├── logs/               ← 投稿履歴（自動生成）
├── scripts/
│   ├── setup_scheduler.bat  ← スケジューラ登録
│   └── test_post.bat        ← テスト実行
└── .env                ← APIキー（GitHubにあげない）
```

## 投稿を止めたいとき
`config/settings.yaml` を開いて、止めたいプラットフォームの `enabled: false` にしてください。
