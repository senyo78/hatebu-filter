"""RSS取得 + フィルタリング本体."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import feedparser
import yaml
from zoneinfo import ZoneInfo

from src.rss_writer import write_rss

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "hatebu_ng.yml"
LOG_PATH = BASE_DIR / "logs" / "hatebu_rejected.jsonl"
JST = ZoneInfo("Asia/Tokyo")


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_url(url: str) -> str:
    """URL正規化: scheme小文字化+http→https, netloc小文字化+www.除去, query/fragment削除."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme == "http":
        scheme = "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return urlunparse((scheme, netloc, parsed.path, "", "", ""))


def get_bookmark_count(entry) -> int:
    for key in ["hatena_bookmarkcount", "bookmarkcount"]:
        if hasattr(entry, key):
            try:
                return int(getattr(entry, key))
            except (ValueError, TypeError):
                pass
    return 0


def check_ng(url: str, title: str, ng_domains: list[str], ng_words: list[str]) -> str | None:
    """NGチェック。該当すれば reject_reason を返す。該当なしは None."""
    for domain in ng_domains:
        if domain in url:
            return f"ng_domain:{domain}"
    for word in ng_words:
        if word in title:
            return f"ng_word:{word}"
    return None


def run() -> None:
    config = load_config()
    feeds_config = config["feeds"]
    ng_domains = config.get("domains", [])
    ng_words = config.get("words", [])

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    seen_urls: set[str] = set()
    accepted: list[dict] = []
    rejected_count = 0
    now = datetime.now(tz=JST)

    for i, feed_info in enumerate(feeds_config):
        feed_url = feed_info["url"]
        label = feed_info["label"]

        if i > 0:
            time.sleep(1)

        try:
            parsed = feedparser.parse(feed_url)
            if parsed.bozo and not parsed.entries:
                raise parsed.bozo_exception  # type: ignore[union-attr]
        except Exception as exc:
            print(f"[WARN] feed={feed_url}: {exc}", file=sys.stderr)
            continue

        for entry in parsed.entries:
            raw_url = entry.get("link", "")
            if not raw_url:
                continue
            norm_url = normalize_url(raw_url)
            if norm_url in seen_urls:
                continue
            seen_urls.add(norm_url)

            title = entry.get("title", "")
            bookmark_count = get_bookmark_count(entry)
            published = entry.get("published", "") or entry.get("updated", "")

            reason = check_ng(norm_url, title, ng_domains, ng_words)

            if reason:
                rejected_count += 1
                log_entry = {
                    "title": title,
                    "url": raw_url,
                    "published": published,
                    "bookmark_count": bookmark_count,
                    "category": label,
                    "feed_url": feed_url,
                    "reject_reason": reason,
                    "rejected_at": now.isoformat(),
                }
                with open(LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            else:
                accepted.append({
                    "title": title,
                    "url": raw_url,
                    "published": published,
                    "bookmark_count": bookmark_count,
                    "category": label,
                    "description": entry.get("summary", ""),
                    "imageurl": entry.get("hatena_imageurl", "") or "",
                })

    write_rss(accepted)
    print(f"accepted: {len(accepted)}, rejected: {rejected_count}")


if __name__ == "__main__":
    run()
