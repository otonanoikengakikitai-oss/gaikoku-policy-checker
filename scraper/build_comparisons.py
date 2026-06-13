"""comparisons_def.py の比較定義を一次ソースで検証し docs/data/comparisons.json を生成する

- 予算額（budget_yen）: 出典が go.jp/lg.jp で、かつ出典（HTML/PDF）に証跡文字列（budget_evidence）が
  現存することを確認。確認できなければ budget_yen を落とし規模注記のみ公開（捏造を出さない）。
- 一人あたり金額（per_person）: 出典ページに証跡文字列が現存するもののみ公開。
- context_note の無い比較は公開しない。
RSシステムには依存しない（FY2026の確定値を各省の一次ソースから直接検証する）。
"""
import datetime
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber

from common import CACHE_DIR, http_get_raw
from comparisons_def import COMPARISONS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data" / "comparisons.json"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")

# 取得済みソーステキストのメモ化（同一URLの再取得を避ける）
_TEXT_CACHE = {}
# PDFのCJK部首（U+2Fxx）等の異体字を正規化して証跡照合の取りこぼしを防ぐ
import unicodedata as _ud


def host_allowed(url):
    host = urlparse(url or "").hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def source_text(url):
    if url in _TEXT_CACHE:
        return _TEXT_CACHE[url]
    text = ""
    if url.lower().endswith(".pdf"):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        dest = CACHE_DIR / ("cmp_" + re.sub(r"\W+", "_", url)[-60:] + ".pdf")
        import urllib.request

        from common import BROWSER_UA, _CTX

        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(req, timeout=90, context=_CTX) as r:
            dest.write_bytes(r.read())
        with pdfplumber.open(dest) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        text = _ud.normalize("NFKC", text)  # CJK部首・全半角・互換文字を正規化
    else:
        raw = http_get_raw(url) or ""
        text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", "", text)
    _TEXT_CACHE[url] = text
    return text


def build_side(side):
    out = {
        "name": side["name"],
        "target": side["target"],
        "budget_yen": None,
        "budget_note": side.get("budget_note", ""),
        "budget_source": side.get("budget_source"),
        "per_person": [],
        "per_person_source": side.get("per_person_source"),
    }
    # 予算額の検証
    if side.get("budget_yen") is not None:
        src = side["budget_source"]["url"]
        if not host_allowed(src):
            print(f"  エラー: 予算出典が一次ソースでない: {src}", file=sys.stderr)
            raise SystemExit(1)
        page = source_text(src)
        if side.get("budget_evidence", "").replace(" ", "") in page:
            out["budget_yen"] = side["budget_yen"]
        else:
            print(
                f"  警告: 予算証跡『{side.get('budget_evidence')}』が出典に見当たらず金額を非公開: {side['name']}",
                file=sys.stderr,
            )
    # 一人あたり金額の検証
    if side.get("per_person"):
        src = side["per_person_source"]["url"]
        if not host_allowed(src):
            print(f"  エラー: 単価出典が一次ソースでない: {src}", file=sys.stderr)
            raise SystemExit(1)
        page = source_text(src)
        for item in side["per_person"]:
            ev = item["evidence"].replace(" ", "")
            if ev in page:
                out["per_person"].append({"label": item["label"], "text": item["text"]})
            else:
                print(f"  警告: 単価証跡が出典に見当たらず非公開: {side['name']} / {item['label']}（{ev}）", file=sys.stderr)
    return out


def run():
    pairs = []
    for comp in COMPARISONS:
        if not comp.get("context_note"):
            print(f"  エラー: context_note の無い比較は公開不可: {comp['id']}", file=sys.stderr)
            raise SystemExit(1)
        pairs.append(
            {
                "id": comp["id"],
                "title": comp["title"],
                "fiscal_year": comp.get("fiscal_year", 2026),
                "context_note": comp["context_note"],
                "sides": [build_side(s) for s in comp["sides"]],
            }
        )
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "fiscal_year": 2026,
        "comparisons": pairs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"比較 {len(pairs)} 組（FY2026・一次ソース検証）→ {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
