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
from tokyo_def import BASIS_NOTE, EXTERNAL_REPORT, ITEMS, SOURCE, TOURISM, TOURISM_NOTE

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

    def to_yen(rec):
        return {
            "name": rec["name"],
            "amount_yen": rec["amount_man"] * 1_000_000,
            "prev_yen": rec["prev_man"] * 1_000_000,
            "delta_yen": rec["delta_man"] * 1_000_000,
        }

    published = []
    for it in ITEMS:
        why = verify(it)
        if why:
            print(f"  警告: 東京都『{it['name']}』を非公開: {why}", file=sys.stderr)
            continue
        published.append({**to_yen(it), "bureau": it["bureau"], "category": it["category"], "sub_programs": it["sub_programs"]})

    if not published:
        print("  エラー: 東京都の公開可能な事業が0件（検証すべて失敗）", file=sys.stderr)
        raise SystemExit(1)

    # 観光・インバウンド予算（対比用）。headlineが検証を通った場合のみ採用。
    tourism = None
    why = verify(TOURISM)
    if why:
        print(f"  警告: 東京都『観光産業の振興』を非公開: {why}", file=sys.stderr)
    else:
        subs = []
        for s in TOURISM.get("sub_items", []):
            sw = verify(s)
            if sw:
                print(f"  警告: 観光内訳『{s['name']}』を非公開: {sw}", file=sys.stderr)
                continue
            subs.append(to_yen(s))
        tourism = {**to_yen(TOURISM), "bureau": TOURISM["bureau"], "sub_items": subs}

    published.sort(key=lambda x: -x["amount_yen"])
    total = sum(p["amount_yen"] for p in published)
    by_bureau = {}
    for p in published:
        by_bureau[p["bureau"]] = by_bureau.get(p["bureau"], 0) + p["amount_yen"]
    contrast_ratio = round(tourism["amount_yen"] / total, 1) if tourism and total else None
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "government": "東京都",
        "fiscal_year": 2026,
        "source": SOURCE,
        "basis_note": BASIS_NOTE,
        "tourism_note": TOURISM_NOTE,
        "total_yen": total,
        "by_bureau": [{"bureau": b, "amount_yen": v} for b, v in sorted(by_bureau.items(), key=lambda x: -x[1])],
        "items": published,
        "tourism": tourism,
        "contrast_ratio": contrast_ratio,
        "external_report": {
            **EXTERNAL_REPORT,
            # NHKの「外国人材確保」と比較すべきは外国人材カテゴリのみ（多文化共生を除く）
            "ours_yen": sum(p["amount_yen"] for p in published if p["category"] == "外国人材"),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    extra = f" / 観光 {tourism['amount_yen']/1e8:,.1f}億円（{contrast_ratio}倍）" if tourism else ""
    print(f"東京都 外国人政策予算 {len(published)} 事業・計 {total/1e8:,.1f}億円{extra}（一次ソース4重検証）→ {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
