"""埼玉・川口の外国人特化予算（多年度）を一次ソースで検証し docs/data/saitama_kawaguchi.json を生成する

各年度について、その年度の出典PDF（川口市 当初予算のポイント）を取得して:
  1. 出典が lg.jp で生存
  2. 事業名がPDF本文に現存
  3. 実額表記がPDF本文に現存（例: 2,966万5千円）
  4. 市の一般会計総額の表記もPDFに現存
を満たした年度・事業のみ公開する（捏造・転記ミス・年度混入の防止）。
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
from saitama_kawaguchi_def import BASIS_NOTE, GOVERNMENT, REGION_LABEL, TREND_NOTE, YEARS

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


def build_year(y):
    src = y["source"]
    if not host_allowed(src["url"]):
        print(f"  エラー: 川口市 {y['fiscal_year_label']} の出典が一次ソースでない", file=sys.stderr)
        raise SystemExit(1)
    text = fetch_pdf_text(src["url"])

    def present(ev):
        return ev.replace(" ", "") in text

    items = []
    for it in y["items"]:
        if not present(it["name_evidence"]):
            print(f"  警告: 川口市 {y['fiscal_year_label']}『{it['name']}』を非公開: 事業名の証跡なし", file=sys.stderr)
            continue
        if not present(it["amount_evidence"]):
            print(f"  警告: 川口市 {y['fiscal_year_label']}『{it['name']}』を非公開: 実額の証跡なし", file=sys.stderr)
            continue
        items.append(
            {
                "name": it["name"],
                "bureau": it["bureau"],
                "category": it["category"],
                "amount_yen": it["amount_yen"],
                "amount_label": it["amount_evidence"],
                "desc": it["desc"],
            }
        )
    if not items:
        print(f"  警告: 川口市 {y['fiscal_year_label']} は検証通過事業0件のためスキップ", file=sys.stderr)
        return None

    city = None
    cg = y.get("city_general_account")
    if cg and present(cg["amount_evidence"]):
        city = {"amount_yen": cg["amount_yen"], "amount_label": cg["amount_evidence"], "label": cg["label"]}
    elif cg:
        print(f"  警告: 川口市 {y['fiscal_year_label']} の一般会計証跡なし。対比は省略", file=sys.stderr)

    total = sum(i["amount_yen"] for i in items)
    return {
        "fiscal_year": y["fiscal_year"],
        "fiscal_year_label": y["fiscal_year_label"],
        "source": src,
        "items": items,
        "foreign_total_yen": total,
        "city_general_account": city,
        "contrast_pct": round(total / city["amount_yen"] * 100, 4) if city else None,
    }


def run():
    years = [r for r in (build_year(y) for y in YEARS) if r]
    if not years:
        print("  エラー: 川口市の公開可能な年度が0件", file=sys.stderr)
        raise SystemExit(1)
    years.sort(key=lambda r: r["fiscal_year"])
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "government": GOVERNMENT,
        "region_label": REGION_LABEL,
        "basis_note": BASIS_NOTE,
        "trend_note": TREND_NOTE,
        "latest": years[-1]["fiscal_year"],
        "years": years,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    spans = " / ".join(f"{r['fiscal_year_label']} {r['foreign_total_yen']/1e4:,.0f}万円" for r in years)
    print(f"埼玉・川口 {len(years)}年度（一次ソース検証）: {spans} → {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
