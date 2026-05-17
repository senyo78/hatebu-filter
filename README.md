# hatebu-filter

> **注記 (2026-05-17)**: 本番配信は **OCI VM の cron** に移行済みです。Inoreader 等の購読フィードは VM 配信(Caddy 経由、10 分間隔)を使用しています。本リポジトリの GitHub Pages 版(`https://senyo78.github.io/hatebu-filter/output/filtered.xml`)は **ロールバック用に残した保険系統** で、GitHub Actions は無効化済みのため出力は更新されません(凍結状態)。以下の手順書は GitHub Actions 時代の元来の構成説明として残しています。

はてなブックマークのホッテントリRSSをNGドメインでフィルタリングし、GitHub Pagesでクリーンなフィードを配信するシステム。却下ログを1日1回メールでダイジェスト送信します。

## 仕組み

```
┌─────────────────┐    ┌──────────────────────────────────┐
│ はてブ RSS (3本) │───>│  GitHub Actions (30分ごと)        │
│  総合 + IT + 経済 │    │  python -m src.filter             │
└─────────────────┘    │    ↓                              │
                       │  NGドメイン判定                    │
                       │    ├─ 通過 → output/filtered.xml  │
                       │    └─ 却下 → logs/rejected.jsonl  │
                       │    ↓                              │
                       │  git commit & push                │
                       └──────────────────────────────────┘
                                      │
                       ┌──────────────┴──────────────┐
                       │  GitHub Pages               │
                       │  filtered.xml を配信         │
                       └─────────────────────────────┘

┌──────────────────────────────────┐
│  GitHub Actions (毎朝 9:00 JST)  │
│  python -m src.mail_digest       │
│    → 却下ダイジェストをメール送信  │
└──────────────────────────────────┘
```

## セットアップ手順

### 1. リポジトリのSecretsを登録

Settings > Secrets and variables > Actions に以下を登録:

| Secret名 | 値 |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Gmailアドレス |
| `SMTP_PASS` | アプリパスワード |
| `MAIL_FROM` | 送信元アドレス |
| `MAIL_TO` | 送信先アドレス |

### 2. GitHub Pagesを有効化

Settings > Pages で:
- Source: **Deploy from a branch**
- Branch: **main** / `/ (root)`

配信URL: `https://<user>.github.io/hatebu-filter/output/filtered.xml`

### 3. ローカル開発

```bash
python -m venv .venv
source .venv/bin/activate   # Windowsは .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # SMTP設定を記入
python -m src.filter        # フィルタ実行
python -m src.mail_digest   # ダイジェスト送信テスト
```

## NGリストの編集方法

`config/hatebu_ng.yml` の `domains` リストを編集してください。

```yaml
domains:
  - example.com        # このドメインを含むURLを却下
  - blog.example.jp/spam  # パス付きで部分一致
```

部分一致で判定されるため、`example.com` と書くと `sub.example.com` もマッチします。

## RSSの登録方法

Feedly等のRSSリーダーに以下のURLを登録:

```
https://<user>.github.io/hatebu-filter/output/filtered.xml
```

Feedlyの場合: https://feedly.com/i/subscription/feed%2Fhttps%3A%2F%2F<user>.github.io%2Fhatebu-filter%2Foutput%2Ffiltered.xml

## ログの見方

却下ログは `logs/hatebu_rejected.jsonl` にJSONL形式で保存されます。

```bash
# 却下理由の集計
cat logs/hatebu_rejected.jsonl | jq -r '.reject_reason' | sort | uniq -c | sort -rn | head -20

# 特定ドメインの却下記事一覧
cat logs/hatebu_rejected.jsonl | jq -r 'select(.reject_reason | contains("hamusoku")) | .title'

# 日別却下数
cat logs/hatebu_rejected.jsonl | jq -r '.rejected_at[:10]' | sort | uniq -c

# ブクマ数上位の却下記事（本当にフィルタすべきか確認）
cat logs/hatebu_rejected.jsonl | jq -s 'sort_by(-.bookmark_count) | .[:10] | .[] | "\(.bookmark_count) users: \(.title)"'
```

## トラブルシューティング

### フィルタが動かない
- Actions タブでワークフローの実行ログを確認
- `[WARN]` 出力がある場合、はてブ側の一時的な障害の可能性あり（次回実行で自動復旧）

### メールが届かない
- Secrets が正しく登録されているか確認
- Gmailの場合、アプリパスワードが必要（通常のパスワードは使えません）
- SMTP_PORT が 587 (STARTTLS) であることを確認

### RSSが更新されない
- GitHub Pagesのビルドが完了しているか確認（Actions > pages build and deployment）
- ブラウザのキャッシュをクリアして再確認

### 特定の記事がフィルタされない
- `config/hatebu_ng.yml` のドメインが正しいか確認（部分一致）
- URLの正規化後のドメインで判定される点に注意（`www.` は除去、`http` は `https` に統一）
