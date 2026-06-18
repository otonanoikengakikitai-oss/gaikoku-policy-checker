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
from saitama_kawaguchi_def import (
    BASIS_NOTE,
    GOVERNMENT,
    PREF_BASIS_NOTE,
    PREF_GOVERNMENT,
    PREF_TREND_NOTE,
    PREF_YEARS,
    REGION_LABEL,
    TREND_NOTE,
    YEARS,
)

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "saitama_kawaguchi.json"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")


def host_allowed(url):
    host = urlparse(url or "").hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def fetch_pdf_text(url, page_slice=None):
    """PDFを取得し本文を返す。page_slice=(start,end) を渡すと該当ページのみ抽出（巨大な県の説明書対策）。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / ("saitama_" + re.sub(r"\W+", "_", url)[-46:] + ".pdf")
    last = None
    for ua in (UA, BROWSER_UA):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=120, context=_CTX) as r:
                dest.write_bytes(r.read())
            break
        except Exception as e:  # noqa: BLE001
            last = e
    else:
        raise RuntimeError(f"埼玉県/川口市PDF取得失敗: {url}: {last}")
    with pdfplumber.open(dest) as pdf:
        pages = pdf.pages[page_slice[0]:page_slice[1]] if page_slice else pdf.pages
        text = "\n".join((p.extract_text() or "") for p in pages)
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))  # 空白除去（カンマは保持）


def build_pref_year(y):
    """埼玉県（県全体）の年度を一次ソースで検証して構築する。
    予算説明書PDF（巨大）は国際交流費の周辺ページのみ抽出して 目名＋金額 を照合し、
    一般会計総額は当初予算案の概要PDFの実額表記で照合する。"""
    src = y["source"]
    ga = y["general_account"]
    if not host_allowed(src["url"]) or not host_allowed(ga["source"]["url"]):
        print(f"  エラー: 埼玉県 {y['fiscal_year_label']} の出典が一次ソースでない", file=sys.stderr)
        raise SystemExit(1)
    # 予算説明書は793ページ前後。国際交流費は概ね p100〜p140 に収まる。
    setsumei = fetch_pdf_text(src["url"], page_slice=(95, 145))
    gaiyou = fetch_pdf_text(ga["source"]["url"])

    def present(ev, text):
        return ev.replace(" ", "") in text

    items = []
    for it in y["items"]:
        if not present(it["name_evidence"], setsumei):
            print(f"  警告: 埼玉県 {y['fiscal_year_label']}『{it['name']}』を非公開: 目名の証跡なし", file=sys.stderr)
            continue
        if not present(it["amount_evidence"], setsumei):
            print(f"  警告: 埼玉県 {y['fiscal_year_label']}『{it['name']}』を非公開: 金額の証跡なし（{it['amount_evidence']}）", file=sys.stderr)
            continue
        items.append({"name": it["name"], "bureau": it["bureau"], "category": it["category"], "amount_yen": it["amount_yen"], "amount_label": _man_label(it["amount_yen"]), "desc": it["desc"]})
    if not items:
        print(f"  警告: 埼玉県 {y['fiscal_year_label']} は検証通過事業0件のためスキップ", file=sys.stderr)
        return None

    general = None
    if present(ga["amount_evidence"], gaiyou):
        general = {"amount_yen": ga["amount_yen"], "amount_label": ga["amount_evidence"], "label": ga["label"], "source": ga["source"]}
    else:
        print(f"  警告: 埼玉県 {y['fiscal_year_label']} の一般会計総額の証跡なし。対比は省略", file=sys.stderr)

    total = sum(i["amount_yen"] for i in items)
    return {
        "fiscal_year": y["fiscal_year"],
        "fiscal_year_label": y["fiscal_year_label"],
        "source": src,
        "items": items,
        "foreign_total_yen": total,
        "general_account": general,
        "contrast_pct": round(total / general["amount_yen"] * 100, 4) if general else None,
    }


def _man_label(yen):
    """円→『X,XXX万Y千円』等の実額ラベル（1円単位の端数も保持）。"""
    oku, rest = divmod(yen, 100000000)
    man, rest = divmod(rest, 10000)
    sen, en = divmod(rest, 1000)
    parts = []
    if oku:
        parts.append(f"{oku:,}億")
    if man or oku:
        parts.append(f"{man:,}万")
    if sen:
        parts.append(f"{sen}千")
    if en:
        parts.append(f"{en}")
    return ("".join(parts) or "0") + "円"


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
    population = None
    pop = y.get("population")
    if pop:
        population = {
            "foreign": pop["foreign"],
            "total": pop["total"],
            "share_pct": round(pop["foreign"] / pop["total"] * 100, 2),
            "as_of": pop["as_of"],
            "source": pop["source"],
        }
    return {
        "fiscal_year": y["fiscal_year"],
        "fiscal_year_label": y["fiscal_year_label"],
        "source": src,
        "items": items,
        "foreign_total_yen": total,
        "city_general_account": city,
        "contrast_pct": round(total / city["amount_yen"] * 100, 4) if city else None,
        "population": population,
    }


def run():
    # 焦点（Spotlight）: 川口市
    spot_years = [r for r in (build_year(y) for y in YEARS) if r]
    if not spot_years:
        print("  エラー: 川口市の公開可能な年度が0件", file=sys.stderr)
        raise SystemExit(1)
    spot_years.sort(key=lambda r: r["fiscal_year"])

    # メイン: 埼玉県（県全体）
    pref_years = [r for r in (build_pref_year(y) for y in PREF_YEARS) if r]
    pref_years.sort(key=lambda r: r["fiscal_year"])
    prefecture = None
    if pref_years:
        prefecture = {
            "government": PREF_GOVERNMENT,
            "basis_note": PREF_BASIS_NOTE,
            "trend_note": PREF_TREND_NOTE,
            "latest": pref_years[-1]["fiscal_year"],
            "years": pref_years,
        }
    else:
        print("  警告: 埼玉県の公開可能な年度が0件（メインは省略し川口のみ）", file=sys.stderr)

    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "government": GOVERNMENT,
        "region_label": REGION_LABEL,
        "prefecture": prefecture,
        "spotlight": {
            "government": GOVERNMENT,
            "basis_note": BASIS_NOTE,
            "trend_note": TREND_NOTE,
            "latest": spot_years[-1]["fiscal_year"],
            "years": spot_years,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    pspan = " / ".join(f"{r['fiscal_year_label']} {r['foreign_total_yen']/1e4:,.0f}万円" for r in pref_years)
    sspan = " / ".join(f"{r['fiscal_year_label']} {r['foreign_total_yen']/1e4:,.0f}万円" for r in spot_years)
    print(f"埼玉県（メイン）: {pspan}", file=sys.stderr)
    print(f"川口市（焦点）: {sspan} → {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
