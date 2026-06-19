"""外国人政策関連ニュースの自動抽出 → docs/data/news.json

公共放送・大手報道（極めて信頼性の高い一次報道メディア）のRSSフィードを複数取得し、
外国人政策に関するキーワードを含む見出しのみを厳格に抽出する。見出し・リンク・配信時刻・
媒体名は原文のまま転記し、当アプリ側の論評・煽りは一切加えない（AdSenseの品質基準に配慮）。

実行: cd scraper && python3 build_news.py
出力: docs/data/news.json（最新最大10件）
"""
import datetime
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

from common import BROWSER_UA, _CTX

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "news.json"
MAX_ITEMS = 10

# 一次報道メディアのRSS（NHK NEWS WEB の各カテゴリ：主要・社会・政治・経済・国際）。
# いずれも記事リンクは一般公開の www3.nhk.or.jp ドメイン。媒体を増やす場合はここに追記する。
FEEDS = [
    {"url": "https://www3.nhk.or.jp/rss/news/cat0.xml", "source": "NHK", "category": "主要"},
    {"url": "https://www3.nhk.or.jp/rss/news/cat1.xml", "source": "NHK", "category": "社会"},
    {"url": "https://www3.nhk.or.jp/rss/news/cat4.xml", "source": "NHK", "category": "政治"},
    {"url": "https://www3.nhk.or.jp/rss/news/cat5.xml", "source": "NHK", "category": "経済"},
    {"url": "https://www3.nhk.or.jp/rss/news/cat6.xml", "source": "NHK", "category": "国際"},
]

# 外国人政策に関するキーワード（政策・制度・共生を中心に。見出しに含まれるものだけ採用）
KEYWORDS = [
    "外国人", "入管", "出入国在留管理", "在留資格", "在留外国人", "技能実習", "育成就労",
    "特定技能", "多文化共生", "難民", "移民", "永住", "帰化", "外国人材", "外国人労働者",
    "日本語教育", "インバウンド", "国際交流", "留学生", "共生社会", "クルド",
]
KW_RE = re.compile("|".join(re.escape(k) for k in KEYWORDS))


def fetch_xml(url):
    """RSS(XML)を取得して文字列で返す。失敗時は None（1フィードの不通で全体を止めない）。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(req, timeout=40, context=_CTX) as r:
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  警告: フィード取得失敗 {url}: {e}", file=sys.stderr)
        return None


def parse_items(xml_text, feed):
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  警告: XML解析失敗 {feed['url']}: {e}", file=sys.stderr)
        return out

    def tag_text(item, name):
        for c in item:
            if c.tag.split("}")[-1] == name:
                return (c.text or "").strip()
        return ""

    for item in root.findall(".//item"):
        title = tag_text(item, "title")
        link = tag_text(item, "link")
        pub = tag_text(item, "pubDate")
        if not title or not link:
            continue
        # 記事リンクは https に正規化（NHK RSS は http 表記のことがある）
        link = re.sub(r"^http://", "https://", link)
        dt = None
        if pub:
            try:
                dt = parsedate_to_datetime(pub)
            except (TypeError, ValueError):
                dt = None
        out.append({
            "title": title,
            "url": link,
            "source": feed["source"],
            "category": feed["category"],
            "dt": dt,
        })
    return out


def run():
    collected = []
    for feed in FEEDS:
        xml_text = fetch_xml(feed["url"])
        if not xml_text:
            continue
        collected.extend(parse_items(xml_text, feed))
    if not collected:
        print("  エラー: ニュースを1件も取得できなかった（全フィード不通）", file=sys.stderr)
        raise SystemExit(1)

    # キーワードで厳格フィルタ（見出しに政策関連語を含むもののみ）
    hits = [it for it in collected if KW_RE.search(it["title"])]

    # リンクで重複排除（複数カテゴリに同記事が載るため）
    seen = set()
    uniq = []
    for it in hits:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)

    # キーワード一致が0件の日は、空で上書きせず直近の good な news.json を温存する。
    if not uniq:
        print("  注意: 外国人政策に関する見出しが0件。既存の news.json を温存（更新なし）", file=sys.stderr)
        if OUT.exists():
            return json.loads(OUT.read_text(encoding="utf-8"))
        # 既存も無い場合のみ空で出力（UI側はitems空ならティッカー非表示）

    # 配信時刻の新しい順。日時不明は末尾へ。
    uniq.sort(key=lambda it: it["dt"] or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
    top = uniq[:MAX_ITEMS]

    items = []
    for it in top:
        dt = it["dt"]
        items.append({
            "title": it["title"],
            "url": it["url"],
            "source": it["source"],
            "category": it["category"],
            "published": dt.astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M") if dt else "",
            "published_iso": dt.isoformat() if dt else "",
        })

    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source_note": (
            "NHK NEWS WEB（公共放送・一次報道）のRSSから、外国人政策に関するキーワードで自動抽出。"
            "見出し・リンク・配信時刻・媒体名は原文のまま。当アプリの論評は加えていません。"
        ),
        "keywords": KEYWORDS,
        "items": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ニュース {len(items)} 件（{len(collected)} 件中・キーワード一致 {len(uniq)} 件）→ {OUT}", file=sys.stderr)
    for it in items:
        print(f"  [{it['published']}] {it['source']}/{it['category']}: {it['title'][:42]}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
