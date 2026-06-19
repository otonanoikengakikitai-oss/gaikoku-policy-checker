"""外国人政策関連ニュースの大量自動抽出 → docs/data/news.json

Google News のキーワード検索RSSで関連最新ニュースを大量取得し、各記事の発信元
（<source url>）ドメインを「全国大手メディア・通信社・NHK等」のホワイトリストで厳格に
絞り込む（Yahoo!ニュース等のポータルや個人ブログ・小規模サイトは除外）。AdSense品質基準に
配慮し、見出し・リンク・配信時刻・媒体名は原文のまま、当アプリの論評は一切加えない。

直近最大50件を news.json にストックする。実行: cd scraper && python3 build_news.py
"""
import datetime
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

from common import BROWSER_UA, _CTX

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "news.json"
MAX_ITEMS = 50
MIN_ITEMS_TO_PUBLISH = 6  # これ未満なら空更新せず直近を温存

# Google News 検索RSS（複数クエリで取りこぼしを最小化）。各クエリ最大100件。
QUERIES = [
    "外国人 OR 入管 OR 出入国在留管理庁 OR 在留資格 OR 在留外国人",
    "技能実習 OR 育成就労 OR 特定技能 OR 外国人材 OR 外国人労働者",
    "多文化共生 OR 難民 OR 移民 OR 日本語教育 OR 外国人住民 OR 共生社会",
]
GNEWS = "https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"

# 信頼できる一次ソース媒体（全国紙・通信社・NHK・主要放送局）。host が一致 or サブドメインのみ採用。
# ポータル（news.yahoo.co.jp 等）・個人ブログ・小規模サイトは載せない＝AdSense対策。
TRUSTED_DOMAINS = (
    "nhk.or.jp",
    "asahi.com", "yomiuri.co.jp", "mainichi.jp", "nikkei.com", "sankei.com",
    "tokyo-np.co.jp", "chunichi.co.jp", "nishinippon.co.jp", "hokkaido-np.co.jp",
    "kahoku.news", "kobe-np.co.jp", "shinmai.co.jp", "kyoto-np.co.jp",
    "kyodo.co.jp", "nordot.app", "47news.jp", "jiji.com",
    "tv-asahi.co.jp", "ntv.co.jp", "tbs.co.jp", "newsdig.tbs.co.jp",
    "fnn.jp", "ann-news.jp", "news24.jp", "fujitv.co.jp",
    "nippon.com", "asahi.co.jp", "mbs.jp", "rkb.jp", "htb.co.jp",
)


def host_trusted(url):
    host = (urlparse(url or "").hostname or "").lower()
    if not host:
        return None
    for d in TRUSTED_DOMAINS:
        if host == d or host.endswith("." + d):
            return d
    return None


def fetch_xml(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(req, timeout=45, context=_CTX) as r:
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  警告: フィード取得失敗 {url[:60]}…: {e}", file=sys.stderr)
        return None


def parse_items(xml_text):
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  警告: XML解析失敗: {e}", file=sys.stderr)
        return out
    for item in root.findall(".//item"):
        d = {c.tag.split("}")[-1]: c for c in item}
        title = (d["title"].text or "").strip() if "title" in d else ""
        link = (d["link"].text or "").strip() if "link" in d else ""
        pub = (d["pubDate"].text or "").strip() if "pubDate" in d else ""
        src_el = d.get("source")
        src_name = (src_el.text or "").strip() if src_el is not None else ""
        src_url = src_el.get("url") if src_el is not None else ""
        if not title or not link:
            continue
        trusted = host_trusted(src_url)
        if not trusted:
            continue  # 信頼ドメイン以外は除外
        # Google の「 - 媒体名」に加え、媒体自身が末尾に「：媒体名」を付ける配信もある（二重）。
        # 末尾の媒体名を区切りごと繰り返し除去する。
        clean = title.strip()
        for _ in range(3):
            prev = clean
            if src_name and clean.endswith(src_name):
                clean = clean[: -len(src_name)].rstrip(" 　-–—|｜:：・")
            if clean == prev:
                break
        # 「画像・写真：…」「動画：…」のように先頭に定型語が付く配信は落とす
        clean = re.sub(r"^(画像・写真|画像|動画|速報|特集)[:：]\s*", "", clean).strip()
        dt = None
        if pub:
            try:
                dt = parsedate_to_datetime(pub)
            except (TypeError, ValueError):
                dt = None
        out.append({
            "title": clean.strip() or title,
            "url": link,  # Google News のリンク（クリックで信頼ソース記事へ転送される）
            "source": src_name or trusted,
            "source_domain": trusted,
            "dt": dt,
        })
    return out


def run():
    collected = []
    for q in QUERIES:
        xml_text = fetch_xml(GNEWS.format(q=urllib.parse.quote(q)))
        if xml_text:
            collected.extend(parse_items(xml_text))
    print(f"  取得（信頼ドメイン通過・重複含む）: {len(collected)} 件", file=sys.stderr)

    # 見出しで重複排除（複数クエリに同記事が載るため）
    seen = set()
    uniq = []
    for it in collected:
        key = re.sub(r"\s+", "", it["title"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)

    # 件数が少なすぎる日は空で上書きせず直近の good な news.json を温存する。
    if len(uniq) < MIN_ITEMS_TO_PUBLISH and OUT.exists():
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        if len(prev.get("items", [])) > len(uniq):
            print(f"  注意: 抽出 {len(uniq)} 件と少数のため直近の news.json（{len(prev['items'])}件）を温存", file=sys.stderr)
            return prev
    if not uniq:
        print("  エラー: 信頼ソースの関連ニュースを取得できなかった", file=sys.stderr)
        raise SystemExit(1)

    uniq.sort(key=lambda it: it["dt"] or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
    top = uniq[:MAX_ITEMS]
    jst = datetime.timezone(datetime.timedelta(hours=9))
    items = []
    for it in top:
        dt = it["dt"]
        items.append({
            "title": it["title"],
            "url": it["url"],
            "source": it["source"],
            "source_domain": it["source_domain"],
            "published": dt.astimezone(jst).strftime("%Y-%m-%d %H:%M") if dt else "",
            "published_iso": dt.isoformat() if dt else "",
        })

    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source_note": (
            "Google ニュースの検索結果から、全国大手メディア・通信社・NHK等の信頼できる発信元の記事のみを"
            "ホワイトリストで抽出（ポータル・個人サイトは除外）。見出し・リンク・配信時刻・媒体名は原文のまま、"
            "当アプリの論評は加えていません。リンクは各媒体の記事へ転送されます。"
        ),
        "queries": QUERIES,
        "items": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ニュース {len(items)} 件（重複排除後 {len(uniq)} 件）→ {OUT}", file=sys.stderr)
    by_src = {}
    for it in items:
        by_src[it["source"]] = by_src.get(it["source"], 0) + 1
    print("  媒体別: " + " / ".join(f"{k}:{v}" for k, v in sorted(by_src.items(), key=lambda x: -x[1])), file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
