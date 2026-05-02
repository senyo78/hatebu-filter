"""フィルタ済みRSS出力."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from dateutil import parser as dateutil_parser
from feedgen.feed import FeedGenerator

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "output" / "filtered.xml"


def _parse_pubdate(date_str: str) -> datetime:
    """日付文字列をtimezone-aware datetimeに変換."""
    if not date_str:
        return datetime.now(tz=timezone.utc)
    try:
        dt = dateutil_parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return datetime.now(tz=timezone.utc)


def write_rss(articles: list[dict]) -> None:
    """accepted記事リストからRSS 2.0を生成し output/filtered.xml に出力."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fg = FeedGenerator()
    fg.title("Hatebu Filtered (NG適用済み)")
    fg.link(href="https://b.hatena.ne.jp/", rel="alternate")
    fg.description("はてなブックマーク ホッテントリ（NGフィルタ適用済み）")
    fg.language("ja")

    for article in articles:
        fe = fg.add_entry()
        bookmark_count = article.get("bookmark_count", 0)
        fe.title(f"{article['title']} [{bookmark_count} users]")
        fe.link(href=article["url"])
        description = article.get("description", "")
        imageurl = article.get("imageurl", "")
        if imageurl:
            html = f'<p><img src="{imageurl}" alt="" /></p>{description}'
            fe.content(html, type="CDATA")
            fe.enclosure(imageurl, "0", "image/jpeg")
        else:
            fe.description(description)
        fe.pubDate(_parse_pubdate(article.get("published", "")))
        fe.category(term=article.get("category", ""))

    # アトミック書き込み: 一時ファイルに書いてrename
    fd, tmp_path = tempfile.mkstemp(
        dir=OUTPUT_PATH.parent, suffix=".tmp", prefix="filtered_"
    )
    try:
        import os
        os.close(fd)
        fg.rss_file(str(tmp_path), pretty=True)
        Path(tmp_path).replace(OUTPUT_PATH)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise
