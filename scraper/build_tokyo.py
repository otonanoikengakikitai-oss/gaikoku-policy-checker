"""東京都の外国人政策予算を一次ソースで検証し docs/data/tokyo.json を生成する

tokyo_def.py の各事業について、出典PDF（東京都財務局 主要事業）を取得して:
  1. 出典が lg.jp で生存
  2. 事業名がPDF本文に現存
  3. 増減チェックサム（amount − prev == delta）
  4. 金額連結（"{amount}{prev}"の数字列）がPDF本文に現存
を満たす事業のみ公開する（捏造・転記ミスの防止）。
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
from tokyo_def import BASIS_NOTE, EXTERNAL_REPORT, ITEMS, POPULATION, SOURCE, TOURISM, TOURISM_NOTE

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "tokyo.json"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")


def host_allowed(url):
    host = urlparse(url or "").hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def fetch_pdf_text(url):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / ("tokyo_" + re.sub(r"\W+", "_", url)[-50:] + ".pdf")
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
        raise RuntimeError(f"東京都PDF取得失敗: {url}: {last}")
    with pdfplumber.open(dest) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    return unicodedata.normalize("NFKC", text)


def run():
    if not host_allowed(SOURCE["url"]):
        print(f"  エラー: 東京都の出典が一次ソースでない: {SOURCE['url']}", file=sys.stderr)
        raise SystemExit(1)
    text = fetch_pdf_text(SOURCE["url"])
    nospace = re.sub(r"\s+", "", text)  # 事業名の証跡照合用（空白のみ除去）
    digits = re.sub(r"[\s,，]+", "", text)  # 金額連結の証跡照合用（空白＋カンマ除去）

    def verify(rec):
        """事業名証跡・増減チェックサム・金額連結証跡の3点を検証し、崩れていれば理由を返す。"""
        a, p, d = rec["amount_man"], rec["prev_man"], rec["delta_man"]
        if rec["name_evidence"].replace(" ", "") not in nospace:
            return f"事業名の証跡なし（{rec['name_evidence']}）"
        if a - p != d:
            return f"増減チェックサム不一致（{a}-{p}≠{d}）"
        if f"{a}{p}" not in digits:
            return f"金額連結の証跡なし（{a}{p}）"
        return None

    # 各事業を4重検証。通過した事業のみ、令和8(amount=当年度)・令和7(prev=前年度)の
    # 両年度を同一PDFから採用する（前年度列も金額連結検証 "{amount}{prev}" に含まれるため検証済み）。
    verified = [it for it in ITEMS if not verify(it)]
    for it in ITEMS:
        why = verify(it)
        if why:
            print(f"  警告: 東京都『{it['name']}』を非公開: {why}", file=sys.stderr)
    if not verified:
        print("  エラー: 東京都の公開可能な事業が0件（検証すべて失敗）", file=sys.stderr)
        raise SystemExit(1)

    # 観光・インバウンド予算（対比用）。headline が検証を通った場合のみ採用。
    tourism_why = verify(TOURISM)
    if tourism_why:
        print(f"  警告: 東京都『観光産業の振興』を非公開: {tourism_why}", file=sys.stderr)
    tourism_subs = []
    if not tourism_why:
        for s in TOURISM.get("sub_items", []):
            sw = verify(s)
            if sw:
                print(f"  警告: 観光内訳『{s['name']}』を非公開: {sw}", file=sys.stderr)
                continue
            tourism_subs.append(s)

    # 年度仕様: 令和8年度は当年度列(amount_man)、令和7年度は前年度列(prev_man)を採用。
    YEAR_SPECS = [
        {
            "fiscal_year": 2026,
            "fiscal_year_label": "令和8年度",
            "key": "amount_man",
            "with_delta": True,
            "source_note": "東京都財務局『令和8年度 主要事業』PDFの当年度列。事業名・増減チェックサム・金額連結の4重検証済み。",
        },
        {
            "fiscal_year": 2025,
            "fiscal_year_label": "令和7年度",
            "key": "prev_man",
            "with_delta": False,
            "source_note": "同『令和8年度 主要事業』PDFの「前年度（令和7年度）」列。金額連結検証で令和8年度額との整合を確認済み。",
        },
    ]

    years = []
    for spec in YEAR_SPECS:
        k = spec["key"]
        items = []
        for it in sorted(verified, key=lambda x: -x[k]):
            entry = {
                "name": it["name"],
                "bureau": it["bureau"],
                "category": it["category"],
                "amount_yen": it[k] * 1_000_000,
                "sub_programs": it["sub_programs"],
            }
            if spec["with_delta"]:
                entry["prev_yen"] = it["prev_man"] * 1_000_000
                entry["delta_yen"] = it["delta_man"] * 1_000_000
            items.append(entry)
        total = sum(e["amount_yen"] for e in items)
        by_bureau = {}
        for e in items:
            by_bureau[e["bureau"]] = by_bureau.get(e["bureau"], 0) + e["amount_yen"]
        tourism = None
        if not tourism_why:
            tourism = {
                "name": TOURISM["name"],
                "bureau": TOURISM["bureau"],
                "amount_yen": TOURISM[k] * 1_000_000,
                "sub_items": [{"name": s["name"], "amount_yen": s[k] * 1_000_000} for s in tourism_subs],
            }
        contrast_ratio = round(tourism["amount_yen"] / total, 1) if tourism and total else None
        year = {
            "fiscal_year": spec["fiscal_year"],
            "fiscal_year_label": spec["fiscal_year_label"],
            "source_note": spec["source_note"],
            "total_yen": total,
            "by_bureau": [{"bureau": b, "amount_yen": v} for b, v in sorted(by_bureau.items(), key=lambda x: -x[1])],
            "items": items,
            "tourism": tourism,
            "contrast_ratio": contrast_ratio,
        }
        if spec["fiscal_year"] == 2026:
            year["external_report"] = {
                **EXTERNAL_REPORT,
                # NHKの「外国人材確保」と比較すべきは外国人材カテゴリのみ（多文化共生を除く）
                "ours_yen": sum(e["amount_yen"] for e in items if e["category"] == "外国人材"),
            }
        pop = POPULATION.get(spec["fiscal_year"])
        if pop:
            year["population"] = {
                "foreign": pop["foreign"],
                "total": pop["total"],
                "share_pct": round(pop["foreign"] / pop["total"] * 100, 2),
                "as_of": pop["as_of"],
                "source": pop["source"],
            }
        years.append(year)

    years.sort(key=lambda y: y["fiscal_year"])
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "government": "東京都",
        "source": SOURCE,
        "basis_note": BASIS_NOTE,
        "tourism_note": TOURISM_NOTE,
        "latest": years[-1]["fiscal_year"],
        "years": years,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    spans = " / ".join(f"{y['fiscal_year_label']} {y['total_yen']/1e8:,.1f}億円" for y in years)
    print(f"東京都 外国人政策予算 {len(verified)} 事業 × {len(years)}年度: {spans}（一次ソース4重検証）→ {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
