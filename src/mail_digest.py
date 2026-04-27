"""却下ログのメール送信."""

from __future__ import annotations

import json
import os
import smtplib
import sys
from collections import Counter
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "logs" / "hatebu_rejected.jsonl"
JST = ZoneInfo("Asia/Tokyo")

# .envが無くてもエラーにしない
load_dotenv(BASE_DIR / ".env", override=False)


def load_recent_logs(hours: int = 24) -> list[dict]:
    """過去N時間分の却下ログを読み込む."""
    if not LOG_PATH.exists():
        return []
    cutoff = datetime.now(tz=JST) - timedelta(hours=hours)
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            rejected_at = entry.get("rejected_at", "")
            try:
                dt = datetime.fromisoformat(rejected_at)
                if dt >= cutoff:
                    entries.append(entry)
            except (ValueError, TypeError):
                continue
    return entries


def build_body(entries: list[dict], now: datetime) -> str:
    """メール本文を生成."""
    yesterday = now - timedelta(hours=24)
    period_from = yesterday.strftime("%Y-%m-%d %H:%M")
    period_to = now.strftime("%Y-%m-%d %H:%M")

    reason_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    for e in entries:
        reason_counter[e.get("reject_reason", "unknown")] += 1
        category_counter[e.get("category", "unknown")] += 1

    lines: list[str] = []
    lines.append("==== サマリー ====")
    lines.append(f"集計期間: {period_from} 〜 {period_to} JST")
    lines.append(f"却下総数: {len(entries)}件")
    lines.append("")

    lines.append("==== 却下理由ランキング ====")
    for i, (reason, count) in enumerate(reason_counter.most_common(), 1):
        lines.append(f" {i:>2}. {reason}  {count}件")
    lines.append("")

    lines.append("==== カテゴリ別却下数 ====")
    for cat, count in category_counter.most_common():
        lines.append(f" {cat + ':':12s} {count}件")
    lines.append("")

    lines.append("==== 却下記事一覧（直近24時間、最大100件） ====")
    for e in entries[:100]:
        reason = e.get("reject_reason", "unknown")
        bcount = e.get("bookmark_count", 0)
        title = e.get("title", "")
        url = e.get("url", "")
        rejected_at = e.get("rejected_at", "")
        category = e.get("category", "")
        try:
            dt = datetime.fromisoformat(rejected_at)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            time_str = rejected_at

        # reject_reason からドメイン部分を抽出
        domain_hint = reason.split(":", 1)[1] if ":" in reason else reason

        lines.append(f"[{reason}] ({bcount}users) {title}")
        lines.append(f"  URL: {url}")
        lines.append(f"  受信: {time_str}")
        lines.append(f"  カテゴリ: {category}")
        lines.append(f'  ↓ 取り消したい場合: NGリストから "{domain_hint}" を削除')
        lines.append("")

    lines.append("==== ヒント ====")
    lines.append("- NGリストを編集: config/hatebu_ng.yml")
    lines.append("- 却下を取り消したい記事があれば、上記コメントの該当ドメインを config から削除")

    return "\n".join(lines)


def send_mail(subject: str, body: str) -> None:
    """SMTP経由でメール送信."""
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    mail_from = os.environ.get("MAIL_FROM", "")
    mail_to = os.environ.get("MAIL_TO", "")

    if not all([host, user, password, mail_from, mail_to]):
        print("SMTP設定が不完全です。環境変数を確認してください。", file=sys.stderr)
        sys.exit(1)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        print(f"ダイジェストメール送信完了: {mail_to}")
    except Exception as exc:
        print(f"メール送信失敗: {exc}", file=sys.stderr)
        sys.exit(1)


def run() -> None:
    entries = load_recent_logs(hours=24)
    now = datetime.now(tz=JST)
    date_str = now.strftime("%Y-%m-%d")
    subject = f"[hatebu-filter] 却下ダイジェスト {date_str} (却下 {len(entries)}件)"
    body = build_body(entries, now)
    send_mail(subject, body)


if __name__ == "__main__":
    run()
