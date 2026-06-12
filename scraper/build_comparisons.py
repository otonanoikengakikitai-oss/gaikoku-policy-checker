"""comparisons_def.py の比較定義を実データで組み立て docs/data/comparisons.json を生成する

- 事業予算: RSシステム取得時のキャッシュ（cache/rs_*.json）から事業名の完全一致で解決
- 一人あたり金額: 出典ページを取得し、証跡文字列が現存するものだけ公開
- 出典が go.jp / lg.jp 以外なら即エラー
"""
import datetime
import glob
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from common import http_get_text
from comparisons_def import COMPARISONS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data" / "comparisons.json"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")


def load_rs_index():
    """キャッシュ済みの全RS事業を {事業名: レコード} に索引化"""
    meta = json.loads((ROOT / "docs" / "data" / "projects.json").read_text(encoding="utf-8"))
    year = meta["fiscal_year"]
    index = {}
    for f in glob.glob(str(ROOT / "cache" / f"rs_{year}_p*.json")):
        for p in json.load(open(f, encoding="utf-8"))["results"]:
            cur = next(
                (
                    b["initial_budgets_total_amount"]
                    for b in (p.get("budget_data") or [])
                    if b.get("fiscal_year") == year and b.get("initial_budgets_total_amount") is not None
                ),
                None,
            )
            index[(p.get("name") or "").strip()] = {
                "budget_yen": cur,
                "ministry": p.get("ministry_name") or "",
                "source_url": f"https://rssystem.go.jp/project/{p['id']}",
            }
    if not index:
        print("  エラー: RSキャッシュが空。先に rs_system.py を実行すること", file=sys.stderr)
        raise SystemExit(1)
    return year, index


def host_allowed(url):
    host = urlparse(url).hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def build_side(side, rs_index, page_cache):
    rs = rs_index.get(side["rs_project_name"])
    if rs is None:
        print(f"  エラー: RS事業名が見つからない: {side['rs_project_name']}", file=sys.stderr)
        raise SystemExit(1)
    out = {
        "name": side["name"],
        "target": side["target"],
        "budget_yen": rs["budget_yen"],
        "ministry": rs["ministry"],
        "rs_source_url": rs["source_url"],
        "per_person": [],
        "per_person_source": side["per_person_source"],
    }
    if side["per_person"]:
        src = side["per_person_source"]["url"]
        if not host_allowed(src):
            print(f"  エラー: 一次ソース以外の出典: {src}", file=sys.stderr)
            raise SystemExit(1)
        if src not in page_cache:
            page_cache[src] = http_get_text(src)
        page = page_cache[src]
        for item in side["per_person"]:
            ev = item["evidence"].replace(" ", "")
            if ev in page:
                out["per_person"].append({"label": item["label"], "text": item["text"]})
            else:
                print(f"  警告: 証跡が出典ページに見当たらず非公開: {side['name']} / {item['label']}（{ev}）", file=sys.stderr)
    return out


def run():
    year, rs_index = load_rs_index()
    page_cache = {}
    pairs = []
    for comp in COMPARISONS:
        if not comp.get("context_note"):
            print(f"  エラー: context_note の無い比較は公開不可: {comp['id']}", file=sys.stderr)
            raise SystemExit(1)
        pairs.append(
            {
                "id": comp["id"],
                "title": comp["title"],
                "context_note": comp["context_note"],
                "sides": [build_side(s, rs_index, page_cache) for s in comp["sides"]],
            }
        )
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "fiscal_year": year,
        "comparisons": pairs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"比較 {len(pairs)} 組 → {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
