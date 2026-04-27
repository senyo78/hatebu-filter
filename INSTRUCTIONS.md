# プロジェクト: hatebu-filter

はてなブックマークのRSSをブラックリスト方式でフィルタリングし、結果のRSSをGitHub Pagesで配信、却下ログを1日1回メールで送るシステムを作ってください。

## 要件

### 機能
1. 7つのはてブRSS（総合 + カテゴリ別6種）を取得
2. NGドメインリストでフィルタリング（ブクマ数による足切りはしない、取りこぼし防止）
3. 通過した記事を1本のRSSファイルに統合出力
4. 却下した記事をJSONL形式でログ保存
5. 1日1回、却下ログのダイジェストをメール送信
6. GitHub Actionsで自動実行（30分ごとにフィルタ、毎朝9:00 JSTにダイジェスト）

### 環境
- Python 3.12
- 標準ライブラリ + feedparser, feedgen, pyyaml, python-dotenv のみ使用
- GitHub Actions (Ubuntu) 上で動作
- ローカル開発はWindows想定

## ファイル構成

````
hatebu-filter/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── .gitattributes
├── config/
│   └── hatebu_ng.yml          # フィード一覧 + NGリスト
├── src/
│   ├── __init__.py
│   ├── filter.py              # RSS取得 + フィルタリング本体
│   ├── rss_writer.py          # フィルタ済みRSS出力
│   └── mail_digest.py         # 却下ログのメール送信
├── output/
│   ├── .gitkeep
│   └── filtered.xml           # 生成RSS（GitHub Pagesで配信）
├── logs/
│   ├── .gitkeep
│   └── hatebu_rejected.jsonl  # 却下ログ（追記式）
└── .github/
    └── workflows/
        ├── filter.yml          # 30分ごと
        └── digest.yml          # 毎朝9:00 JST
````

## config/hatebu_ng.yml

```yaml
# ============================================================
# 購読するフィード一覧
# カテゴリホッテントリは10〜15ブクマ以上、総合は20〜30ブクマ以上で
# 既にはてブ側の足切りがかかっている。これ以上の足切りはしない（取りこぼし防止）
# ============================================================
feeds:
  - url: https://b.hatena.ne.jp/hotentry.rss
    label: top
  - url: https://b.hatena.ne.jp/hotentry/it.rss
    label: it
  - url: https://b.hatena.ne.jp/hotentry/economics.rss
    label: economics
  - url: https://b.hatena.ne.jp/hotentry/social.rss
    label: social
  - url: https://b.hatena.ne.jp/hotentry/knowledge.rss
    label: knowledge
  - url: https://b.hatena.ne.jp/hotentry/game.rss
    label: game
  - url: https://b.hatena.ne.jp/hotentry/life.rss
    label: life

# ============================================================
# NGドメイン（部分一致でURLに含まれていたら却下）
# ============================================================
domains:
  # ----- 2ch/5chまとめブログ系 -----
  - blog.livedoor.jp/dqnplus              # DQN+
  - blog.livedoor.jp/kinisoku              # 気になるニュース速報
  - blog.livedoor.jp/itsoku                # IT速報
  - blog.livedoor.jp/news23vip             # NEWS23VIP
  - blog.livedoor.jp/nwknews               # ネトウヨ系まとめ
  - blog.livedoor.jp/insidears             # インサイドアース
  - blog.livedoor.jp/goldennews            # ゴールデンニュース
  - blog.livedoor.jp/bluejay01-review      # ブルージェイレビュー
  - blog.livedoor.jp/chihhylove            # ちひいラブ
  - blog.esuteru.com                       # はちま起稿
  - jin115.com                             # オレ的ゲーム速報＠JIN
  - hamusoku.com                           # ハム速
  - himasoku.com                           # 暇つぶしニュース
  - alfalfalfa.com                         # アルファルファモザイク
  - news4vip.livedoor.biz                  # ニュー速VIPブログ
  - michaelsan.livedoor.biz                # ミカエル
  - oryouri.2chblog.jp                     # おーるじゃんる
  - gahalog.2chblog.jp                     # がはろぐ
  - i2chmeijin.blog.fc2.com                # 2ch名人
  - tsuisoku.com                           # ついっぷる速報
  - warotanikki.com                        # ワロタニッキ
  - exawarosu.net                          # エアログ
  - kijosoku.com                           # 鬼女速
  - matomedane.jp                          # まとめだね
  - anonymous-post.mobi                    # 匿名速報
  - onecall2ch.com                         # ワンコール2ch
  - tozanchannel.blog.jp                   # 登山ちゃんねる
  - syurabahazard.com                      # 修羅場ハザード
  - kenmomatome.blog.jp                    # ケンモまとめ
  - kekkongo                               # 結婚速報系
  - katasumisokuhou.blog.jp                # 片隅速報
  - machipatome.publog.jp                  # まちぱとめ
  - oboega-01.blog.jp                      # おぼえがき
  - geinoucv.officialblog.jp               # 芸能CV
  - 3ten5jigen.officialblog.jp             # 三点五次元
  - bimatome.weblog.to                     # 美まとめ
  - galapgs.com                            # ガラパゴス
  - giko-neko.com                          # ギコ猫
  - kawaiisokuhou.com                      # かわいい速報
  - pochisoku.net                          # ぽち速
  - v-classic.com                          # Vクラシック
  - yaraon-blog.com                        # やらおん！
  # ----- バイラル/低品質ニュース系 -----
  - hosyusokuhou.jp                        # 保守速報
  - netgeek.biz                            # netgeek（フェイクニュース常習）
  - tocana.jp                              # TOCANA（オカルト）
  # ----- SEOコンテンツファーム系 -----
  - macholog.com                           # マッチョログ

# NGワード（当面は無効）
words: []

# NGユーザー（はてブRSSにブクマユーザー情報は無いので未対応）
users: []
```

## src/filter.py

要件:
- `config/hatebu_ng.yml` を読み込む
- 全フィードを順次取得（feedparser使用）
- 各リクエスト間に1秒sleep
- フィード取得失敗は個別にcatchして他は継続
- URLの正規化で重複排除してから判定
- 各エントリーをドメイン・ワードで判定
- 通過したものはRSS出力、却下はJSONLログに追記
- 標準出力に `accepted: N, rejected: M` を表示

### URL正規化のルール
- scheme: 小文字化、httpはhttpsに統一
- netloc: 小文字化、先頭の `www.` は除去
- path: そのまま
- query, fragment: 削除

### ブクマ数取得
feedparserでパース後、エントリーのキーは `hatena_bookmarkcount` か `bookmarkcount` のどちらか:
```python
def get_bookmark_count(entry):
    for key in ["hatena_bookmarkcount", "bookmarkcount"]:
        if hasattr(entry, key):
            try:
                return int(getattr(entry, key))
            except (ValueError, TypeError):
                pass
    return 0
```

### 却下ログの1行例
```json
{"title":"...","url":"...","published":"...","bookmark_count":523,"category":"top","feed_url":"...","reject_reason":"ng_domain:hamusoku.com","rejected_at":"2026-04-27T12:30:00+09:00"}
```

## src/rss_writer.py

- accepted の記事一覧を `output/filtered.xml` にRSS 2.0で出力
- フィードタイトル: "Hatebu Filtered (NG適用済み)"
- 各itemに以下を含める:
  - title（末尾に `[N users]` を付加）
  - link
  - description
  - pubDate
  - category（feedのlabel）
- ファイル書き込みはアトミック（一時ファイルに書いてrename）

## src/mail_digest.py

要件:
- `logs/hatebu_rejected.jsonl` を読み、過去24時間分のログを集計
- メール本文をプレーンテキストで生成し送信

### メール本文の構成
````
件名: [hatebu-filter] 却下ダイジェスト 2026-04-27 (却下 N件)

==== サマリー ====
集計期間: 2026-04-26 09:00 〜 2026-04-27 09:00 JST
却下総数: N件

==== 却下理由ランキング ====
 1. ng_domain:hamusoku.com  12件
 2. ng_domain:jin115.com     8件
...

==== カテゴリ別却下数 ====
 top:        25件
 social:     12件
...

==== 却下記事一覧（直近24時間、最大100件） ====
[ng_domain:hamusoku.com] (523users) 記事タイトル
  URL: https://hamusoku.com/...
  受信: 2026-04-27 02:30
  カテゴリ: top
  ↓ 取り消したい場合: NGリストから "hamusoku.com" を削除

==== ヒント ====
- NGリストを編集: config/hatebu_ng.yml
- 却下を取り消したい記事があれば、上記コメントの該当ドメインを config から削除
````

### SMTP設定
環境変数から読み込む:
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_FROM, MAIL_TO

`smtplib` + `email.message.EmailMessage`、STARTTLS対応。
ローカルテスト時は `python-dotenv` で `.env` から読み込むが、GitHub Actions上では `os.environ` から直接読む（dotenvが`.env`を見つけられなくてもエラーにしない）。

エラー時はstderrにログ出して exit 1。

## requirements.txt
````
feedparser>=6.0
feedgen>=1.0
pyyaml>=6.0
python-dotenv>=1.0
````

## .env.example
````
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
MAIL_FROM=
MAIL_TO=
````

## .gitignore
````
.env
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
.pytest_cache/
````

注: `output/` と `logs/` はリポジトリにcommitする（GitHub Actionsで生成→pushする運用のため）。

## .gitattributes
````
* text=auto eol=lf
*.bat text eol=crlf
*.ps1 text eol=crlf
````

## .github/workflows/filter.yml

```yaml
name: hatebu-filter

on:
  schedule:
    - cron: "*/30 * * * *"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: hatebu-filter
  cancel-in-progress: false

jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - run: pip install -r requirements.txt

      - name: Run filter
        run: python -m src.filter

      - name: Commit results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add output/filtered.xml logs/hatebu_rejected.jsonl
          git diff --staged --quiet || git commit -m "update feed [skip ci]"
          git push
```

## .github/workflows/digest.yml

```yaml
name: hatebu-digest

on:
  schedule:
    - cron: "0 0 * * *"   # UTC 0:00 = JST 9:00
  workflow_dispatch:

jobs:
  digest:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - run: pip install -r requirements.txt

      - name: Send digest mail
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASS: ${{ secrets.SMTP_PASS }}
          MAIL_FROM: ${{ secrets.MAIL_FROM }}
          MAIL_TO: ${{ secrets.MAIL_TO }}
        run: python -m src.mail_digest
```

## README.md

以下のセクションで作成:
1. プロジェクト概要
2. 仕組み（GitHub Actions + GitHub Pages構成の図解）
3. セットアップ手順（Secrets登録、Pages有効化）
4. NGリストの編集方法
5. RSSの登録方法（FeedlyのURL例）
6. ログの見方（jq集計コマンド例）
7. トラブルシューティング

## 実装上の注意

- ファイル読み書きは必ず `encoding="utf-8"` を指定（Windowsでも動くように）
- パスは `pathlib.Path` で扱う
- `feedgen` でRSS生成時、各itemのpubDateにはtimezone aware datetimeを渡す
- ログファイルは追記モード(`"a"`)
- 初回実行時に `logs/` `output/` ディレクトリが無ければ作成（`Path.mkdir(parents=True, exist_ok=True)`）
- JSONLは `ensure_ascii=False` で日本語そのまま
- タイムゾーンは `zoneinfo.ZoneInfo("Asia/Tokyo")` を使用
- feedparser のパースエラーは個別にcatchして他のフィードは継続
- フィード取得失敗時は標準エラーに `[WARN] feed=URL: error message` を出力するが処理継続