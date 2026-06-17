"""埼玉・川口の外国人特化予算を一次ソースで検証し docs/data/saitama_kawaguchi.json を生成する

各事業について、出典PDF（川口市 令和7年度 当初予算のポイント）を取得して:
  1. 出典が lg.jp で生存
  2. 事業名がPDF本文に現存
  3. 実額表記がPDF本文に現存（例: 2,966万5千円）
  4. 対比に使う市の一般会計総額の表記もPDFに現存
を満たすもののみ公開する（捏造・転記ミスの防止）。
"""
import datetime
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber

from common import CACHE_DIR, BROWSER_UA, UA, _CTX
from saitama_kawaguchi_def import (
    BASIS_NOTE,
    CITY_GENERAL_ACCOUNT,
    FISCAL_LABEL,
    FISCAL_YEAR,
    ITEMS,
    SOURCE,
    TREND_NOTE,
)

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "saitama_kawaguchi.json"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")


def host_allowed(url):
    host = urlparse(url or "").hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def fetch_pdf_text(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / ("kawaguchi_" + re.sub(r"\W+", "_", url)[-46:] + ".pdf")
    last = None
    for ua in (UA, BROWSER_UA):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=90, context=_CTX) as r:
                dest.write_bytes(r.read())
            break
        except Exception as e:  # noqa: BLE001
            last = e
    else:
        raise RuntimeError(f"川口市PDF取得失敗: {url}: {last}")
    with pdfplumber.open(dest) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))  # 空白除去（カンマは保持）


def run():
    if not host_allowed(SOURCE["url"]):
        print(f"  エラー: 川口市の出典が一次ソースでない: {SOURCE['url']}", file=sys.stderr)
        raise SystemExit(1)
    text = fetch_pdf_text(SOURCE["url"])

    def present(ev):
        return ev.replace(" ", "") in text

    published = []
    for it in ITEMS:
        if not present(it["name_evidence"]):
            print(f"  警告: 川口市『{it['name']}』を非公開: 事業名の証跡なし", file=sys.stderr)
            continue
        if not present(it["amount_evidence"]):
            print(f"  警告: 川口市『{it['name']}』を非公開: 実額の証跡なし（{it['amount_evidence']}）", file=sys.stderr)
            continue
        published.append(
            {
                "name": it["name"],
                "bureau": it["bureau"],
                "category": it["category"],
                "amount_yen": it["amount_yen"],
                "amount_label": it["amount_evidence"],
                "desc": it["desc"],
            }
        )

    if not published:
        print("  エラー: 川口市の公開可能な事業が0件（検証すべて失敗）", file=sys.stderr)
        raise SystemExit(1)

    city = None
    if present(CITY_GENERAL_ACCOUNT["amount_evidence"]):
        city = {
            "amount_yen": CITY_GENERAL_ACCOUNT["amount_yen"],
            "amount_label": CITY_GENERAL_ACCOUNT["amount_evidence"],
            "label": CITY_GENERAL_ACCOUNT["label"],
        }
    else:
        print("  警告: 市の一般会計総額の証跡なし。対比は省略", file=sys.stderr)

    foreign_total = sum(p["amount_yen"] for p in published)
    ratio_pct = round(foreign_total / city["amount_yen"] * 100, 4) if city else None
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "government": "埼玉県川口市",
        "region_label": "埼玉・川口（トレンド焦点）",
        "fiscal_year": FISCAL_YEAR,
        "fiscal_year_label": FISCAL_LABEL,
        "source": SOURCE,
        "basis_note": BASIS_NOTE,
        "trend_note": TREND_NOTE,
        "items": published,
        "foreign_total_yen": foreign_total,
        "city_general_account": city,
        "contrast_pct": ratio_pct,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    pct = f"（市一般会計の約{ratio_pct}%）" if ratio_pct is not None else ""
    print(f"埼玉・川口 外国人特化予算 {len(published)} 事業・計 {foreign_total/1e8:,.3f}億円{pct}（一次ソース検証）→ {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
