"""行政事業レビュー見える化サイト（RSシステム）アダプタ

https://rssystem.go.jp/ の公開APIから対象年度の予算事業を全件取得し、
外国人政策関連キーワードで機械抽出して docs/data/projects.json に正規化する。

- サーバー側の検索APIはキーワードを無視するため、全件取得→ローカル照合方式を採る
- 金額は「事業全体の当初予算額」。外国人対象分のみの切り出し額ではない（UI側で明示）
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

from common import http_get_json

BASE = "https://rssystem.go.jp"
PAGE_SIZE = 500
KEYWORDS = ["外国人", "留学生", "多文化共生", "技能実習", "特定技能", "難民", "在留"]
# 「在留」が海外在住の日本人向け事業（在留邦人保護等）に誤反応しないよう、照合前に除去する
EXCLUDE_PHRASES = ["在留邦人"]

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
N_YEARS = 3  # 直近何年度分を取得するか（APIに存在する年度から動的に選ぶ）


def available_fiscal_years():
    return sorted(http_get_json(f"{BASE}/api/projects/fiscal-years/"))


def fetch_year(year, use_cache=False):
    projects, page = [], 1
    while True:
        data = http_get_json(
            f"{BASE}/api/projects/?fiscal_year={year}&page_size={PAGE_SIZE}&page={page}",
            cache_key=f"rs_{year}_p{page}.json",
            use_cache=use_cache,
        )
        projects.extend(data["results"])
        print(f"  FY{year} page {page}: {len(projects)}/{data['count']}", file=sys.stderr)
        if not data.get("next"):
            break
        page += 1
    return projects


def _clean(text):
    text = text or ""
    for ph in EXCLUDE_PHRASES:
        text = text.replace(ph, "")
    return text


def match_keywords(p):
    """事業名・概要・目的にキーワードが含まれるか。事業名ヒットは relevance=high"""
    name = _clean(p.get("name"))
    body = _clean(p.get("overview")) + _clean(p.get("purpose"))
    hits_name = [k for k in KEYWORDS if k in name]
    hits_body = [k for k in KEYWORDS if k in body]
    hits = sorted(set(hits_name + hits_body), key=KEYWORDS.index)
    if not hits:
        return None, None
    return hits, ("high" if hits_name else "medium")


def normalize(p, hits, relevance, year):
    budgets = sorted(
        (
            {"year": b["fiscal_year"], "amount_yen": b["initial_budgets_total_amount"]}
            for b in (p.get("budget_data") or [])
            if b.get("initial_budgets_total_amount") is not None
        ),
        key=lambda b: b["year"],
    )
    current = next(
        (b["amount_yen"] for b in budgets if b["year"] == year),
        budgets[-1]["amount_yen"] if budgets else None,
    )
    # 事業概要は一切省略しない（全文を保持）。改行のみ正規化する。
    overview = (p.get("overview") or "").strip().replace("\r", "")
    return {
        "id": p["id"],
        "name": (p.get("name") or "").strip(),
        "ministry": p.get("ministry_name") or "",
        "sheet_type": p.get("sheet_type"),
        "fiscal_year": year,
        "keywords": hits,
        "relevance": relevance,
        "budget_yen": current,
        "budgets": budgets,
        "overview": overview,
        "start_year": p.get("start_year"),
        "source_url": f"{BASE}/project/{p['id']}",
    }


def build_year(year, use_cache=False):
    print(f"行政事業レビュー FY{year} を全件取得中…", file=sys.stderr)
    raw = fetch_year(year, use_cache=use_cache)
    matched = []
    for p in raw:
        hits, relevance = match_keywords(p)
        if hits:
            matched.append(normalize(p, hits, relevance, year))
    matched.sort(key=lambda r: (r["budget_yen"] is None, -(r["budget_yen"] or 0)))
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "fiscal_year": year,
        "source": {"name": "行政事業レビュー見える化サイト（RSシステム）", "url": BASE},
        "keywords": KEYWORDS,
        "total_projects_scanned": len(raw),
        "amount_note": "金額は各事業全体の当初予算額であり、外国人対象分のみを切り出した額ではない",
        "projects": matched,
    }
    path = DATA_DIR / f"projects_{year}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  FY{year}: 抽出 {len(matched)} 事業（走査 {len(raw)}）→ {path.name}", file=sys.stderr)
    return out


def run(years=None, use_cache=False):
    if not years:
        years = available_fiscal_years()[-N_YEARS:]
    years = sorted(years)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    latest_out = None
    for year in years:
        latest_out = build_year(year, use_cache=use_cache)
    # 後方互換: projects.json は最新年度のコピー（比較ビルド等が参照）
    (DATA_DIR / "projects.json").write_text(json.dumps(latest_out, ensure_ascii=False, indent=1), encoding="utf-8")
    years_meta = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "years": years,
        "latest": years[-1],
    }
    (DATA_DIR / "years.json").write_text(json.dumps(years_meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"対象年度 {years} → years.json", file=sys.stderr)
    return latest_out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=str, default=None, help="カンマ区切り（例: 2024,2025）。省略時はAPIの最新3年度")
    ap.add_argument("--use-cache", action="store_true")
    args = ap.parse_args()
    run(years=[int(y) for y in args.years.split(",")] if args.years else None, use_cache=args.use_cache)
