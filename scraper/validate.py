"""公開前の品質ゲート（CIで強制）

- 全レコードの source_url が go.jp / lg.jp ドメインであること
- 必須フィールドの存在・型
- 違反が1件でもあれば exit 1 で公開を止める
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")


def host_allowed(url):
    host = urlparse(url).hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def check_projects(errors):
    years_meta = json.loads((DATA_DIR / "years.json").read_text(encoding="utf-8"))
    if not years_meta.get("years"):
        errors.append("years.json: 対象年度が空")
        return 0
    total = 0
    for year in years_meta["years"]:
        total += check_projects_file(DATA_DIR / f"projects_{year}.json", errors)
    check_projects_file(DATA_DIR / "projects.json", errors)  # 最新年度のコピーも検証
    return total


def check_projects_file(path, errors):
    data = json.loads(path.read_text(encoding="utf-8"))
    for p in data["projects"]:
        where = f"projects/{p.get('id', '?')}"
        if not p.get("name"):
            errors.append(f"{where}: name が空")
        if not p.get("ministry"):
            errors.append(f"{where}: ministry が空")
        if not p.get("keywords"):
            errors.append(f"{where}: keywords が空（抽出根拠の明示は必須）")
        if p.get("relevance") not in ("high", "medium"):
            errors.append(f"{where}: relevance 不正")
        if not p.get("source_url") or not host_allowed(p["source_url"]):
            errors.append(f"{where}: source_url が一次ソースでない: {p.get('source_url')}")
        b = p.get("budget_yen")
        if b is not None and (not isinstance(b, int) or b < 0):
            errors.append(f"{where}: budget_yen 不正: {b!r}")
    if not data.get("amount_note"):
        errors.append(f"{path.name}: amount_note（金額の注記）は必須")
    return len(data["projects"])


def check_claims(errors):
    path = DATA_DIR / "claims.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for c in data["claims"]:
        where = f"claims/{c.get('id', '?')}"
        if c.get("verdict") not in ("true", "false", "conditional", "misleading"):
            errors.append(f"{where}: verdict 不正")
        if not c.get("fact"):
            errors.append(f"{where}: fact が空")
        srcs = c.get("sources") or []
        if not srcs:
            errors.append(f"{where}: 出典なしの言説は公開不可")
        for s in srcs:
            if not host_allowed(s.get("url", "")):
                errors.append(f"{where}: 一次ソース以外の出典: {s.get('url')}")
    return len(data["claims"])


def check_comparisons(errors):
    path = DATA_DIR / "comparisons.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for c in data["comparisons"]:
        where = f"comparisons/{c.get('id', '?')}"
        if not (c.get("context_note") or "").strip():
            errors.append(f"{where}: context_note（条件差の注記）は必須")
        sides = c.get("sides") or []
        if len(sides) < 2:
            errors.append(f"{where}: 比較には2サイド以上が必要")
        for s in sides:
            if not s.get("name") or not s.get("target"):
                errors.append(f"{where}: サイドの name / target は必須")
            bs = s.get("budget_source")
            if s.get("budget_yen") is not None and (not bs or not host_allowed(bs.get("url", ""))):
                errors.append(f"{where}: 予算額の出典が一次ソースでない: {(bs or {}).get('url')}")
            pps = s.get("per_person_source")
            if s.get("per_person") and (not pps or not host_allowed(pps.get("url", ""))):
                errors.append(f"{where}: 一人あたり金額の出典が一次ソースでない")
            b = s.get("budget_yen")
            if b is not None and (not isinstance(b, int) or b < 0):
                errors.append(f"{where}: budget_yen 不正: {b!r}")
    return len(data["comparisons"])


def check_stats(errors):
    path = DATA_DIR / "stats.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not host_allowed(data.get("source", {}).get("url", "")):
        errors.append(f"stats: 出典が一次ソースでない: {data.get('source', {}).get('url')}")
    for key, ind in data["indicators"].items():
        if not ind.get("series"):
            errors.append(f"stats/{key}: 系列が空")
        for s in ind.get("series", []):
            if not isinstance(s.get("value"), int) or s["value"] < 0:
                errors.append(f"stats/{key}: 値が不正: {s!r}")
        la = ind.get("latest_actual")
        if la:
            if not isinstance(la.get("value"), int) or la["value"] < 0:
                errors.append(f"stats/{key}: latest_actual値が不正")
            if not host_allowed((la.get("source") or {}).get("url", "")):
                errors.append(f"stats/{key}: latest_actualの出典が一次ソースでない: {(la.get('source') or {}).get('url')}")
            if not (la.get("as_of") or "").strip():
                errors.append(f"stats/{key}: latest_actualに基準日(as_of)が無い")
    return len(data["indicators"])


def check_policy_budget(errors):
    path = DATA_DIR / "policy_budget.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not (data.get("scope_note") or "").strip():
        errors.append("policy_budget: scope_note（集計範囲拡大の注記）は必須")
    series = data.get("initial_budget_series") or []
    if len(series) < 2:
        errors.append("policy_budget: 当初予算系列が2年度未満")
    for s in series:
        if not isinstance(s.get("amount_yen"), int) or s["amount_yen"] < 0:
            errors.append(f"policy_budget/{s.get('year')}: amount_yen 不正")
        if not host_allowed((s.get("source") or {}).get("url", "")):
            errors.append(f"policy_budget/{s.get('year')}: 出典が一次ソースでない")
    fy = data.get("fy2026") or {}
    if not fy.get("reconciled"):
        errors.append("policy_budget/fy2026: 施策合算と公式合計の検算が未通過")
    for it in fy.get("top_items", []):
        if not isinstance(it.get("amount_yen"), int):
            errors.append("policy_budget/fy2026: top_item金額が不正")
    if not host_allowed((data.get("primary_source") or {}).get("url", "")):
        errors.append("policy_budget: primary_source が一次ソースでない")
    return len(series)


REQUIRED_TERMS = ["行政事業レビュー", "当初予算", "補正予算", "交付金", "総合的対応策"]


def check_glossary(errors):
    path = DATA_DIR / "glossary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    terms = {t.get("term"): t for t in data.get("terms", [])}
    for req in REQUIRED_TERMS:
        if req not in terms:
            errors.append(f"glossary: 必須用語『{req}』が未収録")
    for term, t in terms.items():
        if not (t.get("def") or "").strip():
            errors.append(f"glossary/{term}: 解説文が空")
    return len(terms)


def check_tokyo(errors):
    path = DATA_DIR / "tokyo.json"
    if not path.exists():
        return 0  # best-effort: 未取得なら検証対象外
    data = json.loads(path.read_text(encoding="utf-8"))
    if not host_allowed((data.get("source") or {}).get("url", "")):
        errors.append("tokyo: 出典が一次ソースでない")
    if not (data.get("basis_note") or "").strip():
        errors.append("tokyo: basis_note（集計基準の注記）は必須")
    items = data.get("items") or []
    if not items:
        errors.append("tokyo: 事業が0件")
    s = 0
    for it in items:
        if not isinstance(it.get("amount_yen"), int) or it["amount_yen"] < 0:
            errors.append(f"tokyo/{it.get('name')}: amount_yen 不正")
        # 増減チェックサム（amount - prev == delta）を公開データでも再確認
        if it.get("amount_yen", 0) - it.get("prev_yen", 0) != it.get("delta_yen"):
            errors.append(f"tokyo/{it.get('name')}: 増減チェックサム不一致")
        s += it.get("amount_yen", 0)
    if s != data.get("total_yen"):
        errors.append("tokyo: total_yen が事業合算と不一致")
    return len(items)


def check_saitama_kawaguchi(errors):
    path = DATA_DIR / "saitama_kawaguchi.json"
    if not path.exists():
        return 0  # best-effort: 未取得なら検証対象外
    data = json.loads(path.read_text(encoding="utf-8"))
    if not host_allowed((data.get("source") or {}).get("url", "")):
        errors.append("saitama_kawaguchi: 出典が一次ソースでない")
    if not (data.get("basis_note") or "").strip():
        errors.append("saitama_kawaguchi: basis_note は必須")
    items = data.get("items") or []
    if not items:
        errors.append("saitama_kawaguchi: 事業が0件")
    s = 0
    for it in items:
        if not isinstance(it.get("amount_yen"), int) or it["amount_yen"] < 0:
            errors.append(f"saitama_kawaguchi/{it.get('name')}: amount_yen 不正")
        s += it.get("amount_yen", 0)
    if s != data.get("foreign_total_yen"):
        errors.append("saitama_kawaguchi: foreign_total_yen が事業合算と不一致")
    return len(items)


def run():
    errors = []
    n_projects = check_projects(errors)
    n_claims = check_claims(errors)
    n_comparisons = check_comparisons(errors)
    n_stats = check_stats(errors)
    n_budget = check_policy_budget(errors)
    n_glossary = check_glossary(errors)
    n_tokyo = check_tokyo(errors)
    n_kawaguchi = check_saitama_kawaguchi(errors)
    if errors:
        print("品質ゲート違反:", file=sys.stderr)
        for e in errors:
            print(f"  NG {e}", file=sys.stderr)
        raise SystemExit(1)
    print(
        f"品質ゲート通過: 事業 {n_projects} 件 / 言説 {n_claims} 件 / 比較 {n_comparisons} 組 / 統計 {n_stats} 指標 / 関係予算 {n_budget} 年度 / 用語 {n_glossary} 語 / 東京都 {n_tokyo} 事業 / 埼玉川口 {n_kawaguchi} 事業、全出典 go.jp/lg.jp",
        file=sys.stderr,
    )


if __name__ == "__main__":
    run()
