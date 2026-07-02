"""大阪府の外国人特化予算（多年度）を一次ソースで4重検証し docs/data/osaka.json を生成する

出典は「大阪府予算編成過程公表」システム（事業別HTML・査定額＝当初予算額が千円単位で明記）と
当初予算(案)資料PDF（一般会計総額）・出入国在留管理庁プレス／大阪府毎月推計人口（人口統計）。
検証（各年度・各事業）:
  1. 出典が lg.jp / go.jp で生存
  2. 事業名が当該事業ページに現存
  3. 当年度査定額と前年度当初の両文字列が同ページに現存
  4. 年度間チェックサム: 当年ページの「前年度当初」＝前年度の査定額（数値照合）
一般会計は前年→当年の金額連結（例: 一般会計31,97232,714742）を証跡として照合し、
人口統計も「大阪府375,319人」等の連結文字列の現存を照合する。1つでも崩れたら非公開。
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

from common import CACHE_DIR, BROWSER_UA, UA, _CTX, http_get_text, http_get_raw
from osaka_def import BASIS_NOTE, BUREAU, GOVERNMENT, TREND_NOTE, YEARS

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "osaka.json"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")


def host_allowed(url):
    host = urlparse(url or "").hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def fetch_pdf_text(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / ("osaka_" + re.sub(r"\W+", "_", url)[-46:] + ".pdf")
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
        raise RuntimeError(f"大阪府PDF取得失敗: {url}: {last}")
    with pdfplumber.open(dest) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))  # 空白除去（カンマは保持）


def fetch_html_text(url):
    """事業別ページ（HTML）のタグ・空白除去済みテキスト。moj.go.jp はブラウザUAが必要。"""
    host = urlparse(url).hostname or ""
    if host.endswith("moj.go.jp"):
        raw = http_get_raw(url)
        if raw is None:
            raise RuntimeError(f"取得失敗: {url}")
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        import html as html_mod
        return re.sub(r"\s+", "", unicodedata.normalize("NFKC", html_mod.unescape(text)))
    return unicodedata.normalize("NFKC", http_get_text(url))


def _man_label(yen):
    """円→『X,XXX万Y千円』等の実額ラベル（端数保持）。"""
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


def build_year(y, prev_amounts):
    """1年度分を検証して構築。prev_amounts = 前年度の {事業名: 査定額円} （年度間チェックサム用）"""
    src = y["source"]
    if not host_allowed(src["url"]):
        print(f"  エラー: 大阪府 {y['fiscal_year_label']} の出典が一次ソースでない", file=sys.stderr)
        raise SystemExit(1)

    items = []
    for it in y["items"]:
        if not host_allowed(it["url"]):
            print(f"  警告: 大阪府『{it['name']}』の出典が一次ソースでない。非公開", file=sys.stderr)
            continue
        try:
            text = fetch_html_text(it["url"])
        except RuntimeError as e:
            print(f"  警告: 大阪府『{it['name']}』のページ取得失敗: {e}。非公開", file=sys.stderr)
            continue
        if it["name_evidence"].replace(" ", "") not in text:
            print(f"  警告: 大阪府 {y['fiscal_year_label']}『{it['name']}』を非公開: 事業名の証跡なし", file=sys.stderr)
            continue
        if it["amount_evidence"] not in text or it["prev_evidence"] not in text:
            print(f"  警告: 大阪府 {y['fiscal_year_label']}『{it['name']}』を非公開: 金額（{it['amount_evidence']}/{it['prev_evidence']}）の証跡なし", file=sys.stderr)
            continue
        # 年度間チェックサム: 当年ページの前年度当初 = 前年度の査定額（前年データがある事業のみ）
        if it["name"] in prev_amounts and prev_amounts[it["name"]] != it["prev_yen"]:
            print(
                f"  警告: 大阪府 {y['fiscal_year_label']}『{it['name']}』を非公開: 年度間チェックサム不一致"
                f"（前年度当初 {it['prev_yen']:,} ≠ 前年度査定 {prev_amounts[it['name']]:,}）",
                file=sys.stderr,
            )
            continue
        items.append(
            {
                "name": it["name"],
                "bureau": BUREAU,
                "category": it["category"],
                "amount_yen": it["amount_yen"],
                "amount_label": _man_label(it["amount_yen"]),
                "prev_yen": it["prev_yen"],
                "delta_yen": it["amount_yen"] - it["prev_yen"],
                "source_url": it["url"],
                "desc": it["desc"],
            }
        )
    if not items:
        print(f"  警告: 大阪府 {y['fiscal_year_label']} は検証通過事業0件のためスキップ", file=sys.stderr)
        return None

    # 一般会計総額（前年→当年の金額連結を証跡として照合）
    general = None
    ga = y.get("general_account")
    if ga and host_allowed(ga["source"]["url"]):
        ga_text = fetch_pdf_text(ga["source"]["url"])
        if ga["amount_evidence"].replace(" ", "") in ga_text:
            general = {"amount_yen": ga["amount_yen"], "amount_label": ga["amount_label"], "label": ga["label"], "source": ga["source"]}
        else:
            print(f"  警告: 大阪府 {y['fiscal_year_label']} の一般会計証跡（{ga['amount_evidence']}）なし。対比は省略", file=sys.stderr)

    # 人口統計（在留外国人数=ISAプレスHTML、総人口=推計人口PDF の証跡照合）
    population = None
    pop = y.get("population")
    if pop and host_allowed(pop["source"]["url"]) and host_allowed(pop["total_source"]["url"]):
        try:
            f_text = fetch_html_text(pop["source"]["url"])
            t_text = fetch_pdf_text(pop["total_source"]["url"])
            if pop["foreign_evidence"] in f_text and pop["total_evidence"] in t_text:
                population = {
                    "foreign": pop["foreign"],
                    "total": pop["total"],
                    "share_pct": round(pop["foreign"] / pop["total"] * 100, 2),
                    "as_of": pop["as_of"],
                    "total_as_of": pop["total_as_of"],
                    "metric_label": pop["metric_label"],
                    "basis": pop["basis"],
                    "source": pop["source"],
                    "total_source": pop["total_source"],
                }
            else:
                print(f"  警告: 大阪府 {y['fiscal_year_label']} の人口統計の証跡なし。統計は省略", file=sys.stderr)
        except RuntimeError as e:
            print(f"  警告: 大阪府 {y['fiscal_year_label']} の人口統計取得失敗: {e}", file=sys.stderr)

    total = sum(i["amount_yen"] for i in items)
    return {
        "fiscal_year": y["fiscal_year"],
        "fiscal_year_label": y["fiscal_year_label"],
        "source": src,
        "items": items,
        "foreign_total_yen": total,
        "general_account": general,
        "contrast_pct": round(total / general["amount_yen"] * 100, 4) if general else None,
        "population": population,
    }


def run():
    years = []
    prev_amounts = {}
    for y in sorted(YEARS, key=lambda r: r["fiscal_year"]):
        r = build_year(y, prev_amounts)
        if r:
            years.append(r)
            prev_amounts = {i["name"]: i["amount_yen"] for i in r["items"]}
    if not years:
        print("  エラー: 大阪府の公開可能な年度が0件", file=sys.stderr)
        raise SystemExit(1)
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "government": GOVERNMENT,
        "basis_note": BASIS_NOTE,
        "trend_note": TREND_NOTE,
        "latest": years[-1]["fiscal_year"],
        "years": years,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    spans = " / ".join(f"{r['fiscal_year_label']} {r['foreign_total_yen']/1e4:,.0f}万円" for r in years)
    print(f"大阪府 {len(years)}年度（一次ソース4重検証）: {spans} → {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
