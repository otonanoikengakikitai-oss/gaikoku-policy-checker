"""都道府県の外国人特化予算（汎用ビルダー） — defモジュール群を4重検証して JSON を生成

47都道府県への横展開の共通基盤。各県の *_def.py は共通スキーマ（GOVERNMENT/OUT_NAME/
BASIS_NOTE/TREND_NOTE/YEARS）でデータと証跡を定義し、本ビルダーが毎回:
  1. 全出典が go.jp / lg.jp で生存していること
  2. 事業名（name_evidence）が出典文書に現存すること
  3. 金額の証跡（amount_evidence・可能なら「事業名＋金額」や「当年＋前年」の連結）が現存すること
  4. 年度間チェックサム（prev_yen があれば前年度の同名事業の額と数値照合）
を満たした事業・年度のみ公開する（捏造・転記ミス・年度混入の防止）。

実行: cd scraper && python3 build_pref.py
"""
import datetime
import html as html_mod
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber

import aichi_def
import ehime_def
import fukuoka_def
import hiroshima_def
import hokkaido_def
import hyogo_def
import kagawa_def
import kanagawa_def
import kyoto_def
import miyagi_def
import okayama_def
from common import CACHE_DIR, BROWSER_UA, UA, _CTX, http_get_raw

DEFS = [hokkaido_def, miyagi_def, aichi_def, fukuoka_def, kanagawa_def, kyoto_def, hyogo_def, hiroshima_def, okayama_def, ehime_def, kagawa_def]

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")
# lg.jp を使わない自治体公式ドメインの明示許可（愛知・神奈川・京都・宮城・岡山・愛媛は pref.*.jp が公式）
EXTRA_ALLOWED_HOSTS = (
    "www.pref.aichi.jp", "pref.aichi.jp",
    "www.pref.kanagawa.jp", "pref.kanagawa.jp",
    "www.pref.kyoto.jp", "pref.kyoto.jp",
    "www.pref.miyagi.jp", "pref.miyagi.jp",
    "www.pref.okayama.jp", "pref.okayama.jp",
    "www.pref.ehime.jp", "pref.ehime.jp",
)

_DOC_CACHE = {}  # url -> 正規化テキスト（同一文書の重複取得を回避）


def host_allowed(url):
    host = urlparse(url or "").hostname or ""
    return host.endswith(ALLOWED_SUFFIXES) or host in EXTRA_ALLOWED_HOSTS


def _norm(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))  # 空白除去（カンマ・括弧は保持）


def fetch_doc(url, doc_type="pdf"):
    """出典文書（PDF/HTML）を取得し正規化テキストを返す。プロセス内でURL単位にキャッシュ。"""
    if url in _DOC_CACHE:
        return _DOC_CACHE[url]
    if doc_type == "html":
        raw = http_get_raw(url)
        if raw is None:
            raise RuntimeError(f"HTML取得失敗: {url}")
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S)
        text = html_mod.unescape(re.sub(r"<[^>]+>", " ", text))
        result = _norm(text)
    else:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        dest = CACHE_DIR / ("pref_" + re.sub(r"\W+", "_", url)[-52:] + ".pdf")
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
            raise RuntimeError(f"PDF取得失敗: {url}: {last}")
        with pdfplumber.open(dest) as pdf:
            result = _norm("\n".join((p.extract_text() or "") for p in pdf.pages))
    _DOC_CACHE[url] = result
    return result


def _man_label(yen):
    """円→『X,XXX万Y千円』等の実額ラベル（端数保持）。"""
    cho, rest = divmod(yen, 10**12)
    oku, rest = divmod(rest, 10**8)
    man, rest = divmod(rest, 10**4)
    sen, en = divmod(rest, 1000)
    parts = []
    if cho:
        parts.append(f"{cho}兆")
    if oku or cho:
        parts.append(f"{oku:,}億")
    if man or oku or cho:
        parts.append(f"{man:,}万")
    if sen:
        parts.append(f"{sen}千")
    if en:
        parts.append(f"{en}")
    return ("".join(parts) or "0") + "円"


def build_year(gov, y, prev_amounts):
    """1年度分を検証して構築。prev_amounts = 前年度の {事業名: 額円}（年度間チェックサム用）"""
    src = y["source"]
    if not host_allowed(src["url"]):
        print(f"  エラー: {gov} {y['fiscal_year_label']} の出典が一次ソースでない", file=sys.stderr)
        raise SystemExit(1)

    items = []
    for it in y["items"]:
        where = f"{gov} {y['fiscal_year_label']}『{it['name']}』"
        if not host_allowed(it["doc"]):
            print(f"  警告: {where} の出典が一次ソースでない。非公開", file=sys.stderr)
            continue
        try:
            text = fetch_doc(it["doc"], it.get("doc_type", "pdf"))
        except RuntimeError as e:
            print(f"  警告: {where} の文書取得失敗: {e}。非公開", file=sys.stderr)
            continue
        if _norm(it["name_evidence"]) not in text:
            print(f"  警告: {where} を非公開: 事業名の証跡なし", file=sys.stderr)
            continue
        if _norm(it["amount_evidence"]) not in text:
            print(f"  警告: {where} を非公開: 金額の証跡なし（{it['amount_evidence']}）", file=sys.stderr)
            continue
        if it.get("prev_evidence") is not None and _norm(it["prev_evidence"]) not in text:
            print(f"  警告: {where} を非公開: 前年度額の証跡なし（{it['prev_evidence']}）", file=sys.stderr)
            continue
        # 年度間チェックサム: 定義された前年度額 = 前年度データの同名事業の額
        if it.get("prev_yen") is not None and it["name"] in prev_amounts and prev_amounts[it["name"]] != it["prev_yen"]:
            print(
                f"  警告: {where} を非公開: 年度間チェックサム不一致"
                f"（前年度当初 {it['prev_yen']:,} ≠ 前年度データ {prev_amounts[it['name']]:,}）",
                file=sys.stderr,
            )
            continue
        entry = {
            "name": it["name"],
            "bureau": it["bureau"],
            "category": it["category"],
            "amount_yen": it["amount_yen"],
            "amount_label": _man_label(it["amount_yen"]),
            "source_url": it["doc"],
            "desc": it["desc"],
        }
        if it.get("prev_yen") is not None:
            entry["prev_yen"] = it["prev_yen"]
            entry["delta_yen"] = it["amount_yen"] - it["prev_yen"]
        items.append(entry)
    if not items:
        print(f"  警告: {gov} {y['fiscal_year_label']} は検証通過事業0件のためスキップ", file=sys.stderr)
        return None

    general = None
    ga = y.get("general_account")
    if ga and host_allowed(ga["source"]["url"]):
        try:
            ga_text = fetch_doc(ga["source"]["url"], ga.get("doc_type", "pdf"))
            if _norm(ga["evidence"]) in ga_text:
                general = {"amount_yen": ga["amount_yen"], "amount_label": ga["amount_label"], "label": ga["label"], "source": ga["source"]}
            else:
                print(f"  警告: {gov} {y['fiscal_year_label']} の一般会計証跡（{ga['evidence'][:24]}…）なし。対比は省略", file=sys.stderr)
        except RuntimeError as e:
            print(f"  警告: {gov} {y['fiscal_year_label']} の一般会計文書取得失敗: {e}", file=sys.stderr)

    population = None
    pop = y.get("population")
    if pop and host_allowed(pop["source"]["url"]) and host_allowed(pop["total_source"]["url"]):
        try:
            f_text = fetch_doc(pop["source"]["url"], pop.get("doc_type", "pdf"))
            t_text = fetch_doc(pop["total_source"]["url"], pop.get("doc_type", "pdf"))
            if _norm(pop["foreign_evidence"]) in f_text and _norm(pop["total_evidence"]) in t_text:
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
                print(f"  警告: {gov} {y['fiscal_year_label']} の人口統計の証跡なし。統計は省略", file=sys.stderr)
        except RuntimeError as e:
            print(f"  警告: {gov} {y['fiscal_year_label']} の人口統計取得失敗: {e}", file=sys.stderr)

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


def build_ga_history(mod):
    """事業データの無い年度の一般会計総額（GA_HISTORY）を証跡照合して構築（任意項目）。"""
    gov = mod.GOVERNMENT
    result = []
    for g in getattr(mod, "GA_HISTORY", []):
        where = f"{gov} {g['fiscal_year_label']} 一般会計（ga_history）"
        if not host_allowed(g["source"]["url"]):
            print(f"  警告: {where} の出典が一次ソースでない。非公開", file=sys.stderr)
            continue
        try:
            text = fetch_doc(g["source"]["url"], g.get("doc_type", "pdf"))
        except RuntimeError as e:
            print(f"  警告: {where} の文書取得失敗: {e}。非公開", file=sys.stderr)
            continue
        if _norm(g["evidence"]) not in text:
            print(f"  警告: {where} を非公開: 金額の証跡なし（{g['evidence'][:24]}…）", file=sys.stderr)
            continue
        entry = {
            "fiscal_year": g["fiscal_year"],
            "fiscal_year_label": g["fiscal_year_label"],
            "amount_yen": g["amount_yen"],
            "amount_label": g["amount_label"],
            "source": g["source"],
        }
        if g.get("note"):
            entry["note"] = g["note"]
        result.append(entry)
    return sorted(result, key=lambda r: r["fiscal_year"])


def build_def(mod):
    gov = mod.GOVERNMENT
    years = []
    prev_amounts = {}
    for y in sorted(mod.YEARS, key=lambda r: r["fiscal_year"]):
        r = build_year(gov, y, prev_amounts)
        if r:
            years.append(r)
            prev_amounts = {i["name"]: i["amount_yen"] for i in r["items"]}
    if not years:
        print(f"  エラー: {gov} の公開可能な年度が0件", file=sys.stderr)
        raise SystemExit(1)
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "government": gov,
        "basis_note": mod.BASIS_NOTE,
        "trend_note": mod.TREND_NOTE,
        "latest": years[-1]["fiscal_year"],
        "years": years,
        "ga_history": build_ga_history(mod),
    }
    dest = DATA_DIR / mod.OUT_NAME
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    spans = " / ".join(f"{r['fiscal_year_label']} {r['foreign_total_yen']/1e4:,.0f}万円" for r in years)
    print(f"{gov} {len(years)}年度（一次ソース4重検証）: {spans} → {dest}", file=sys.stderr)
    return out


def run():
    for mod in DEFS:
        build_def(mod)


if __name__ == "__main__":
    run()
