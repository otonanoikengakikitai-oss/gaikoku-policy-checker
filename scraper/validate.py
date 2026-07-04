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
# lg.jp を使わない自治体公式ドメインの明示許可（愛知・神奈川・京都・宮城・岡山・愛媛・静岡・熊本は pref.*.jp が公式）
EXTRA_ALLOWED_HOSTS = (
    "www.pref.aichi.jp", "pref.aichi.jp",
    "www.pref.kanagawa.jp", "pref.kanagawa.jp",
    "www.pref.kyoto.jp", "pref.kyoto.jp",
    "www.pref.miyagi.jp", "pref.miyagi.jp",
    "www.pref.okayama.jp", "pref.okayama.jp",
    "www.pref.ehime.jp", "pref.ehime.jp",
    "www.pref.shizuoka.jp", "pref.shizuoka.jp",
    "www.pref.kumamoto.jp", "pref.kumamoto.jp",
    "www.pref.ibaraki.jp", "pref.ibaraki.jp",
    "www.pref.okinawa.jp", "pref.okinawa.jp",
    "www.pref.gunma.jp", "pref.gunma.jp",
    "www.pref.toyama.jp", "pref.toyama.jp",
    "www.pref.iwate.jp", "pref.iwate.jp",
    "www.pref.yamagata.jp", "pref.yamagata.jp",
)


def host_allowed(url):
    host = urlparse(url).hostname or ""
    return host.endswith(ALLOWED_SUFFIXES) or host in EXTRA_ALLOWED_HOSTS


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
    # 国タブの年度連動用 national_by_fy（各会計年度の全国統計）を検証
    nbf = data.get("national_by_fy") or {}
    if not nbf:
        errors.append("stats: national_by_fy（国タブの年度別統計）が空")
    for fy, r in nbf.items():
        w = f"stats/national_by_fy/{fy}"
        for k in ("foreign", "total"):
            if not isinstance(r.get(k), int) or r[k] <= 0:
                errors.append(f"{w}: {k} 不正: {r.get(k)!r}")
        if not isinstance(r.get("share_pct"), (int, float)):
            errors.append(f"{w}: share_pct 不正")
        if not (r.get("foreign_as_of") or "").strip():
            errors.append(f"{w}: foreign_as_of（基準日）が無い")
        if not host_allowed((r.get("foreign_source") or {}).get("url", "")):
            errors.append(f"{w}: 在留外国人数の出典が一次ソースでない: {(r.get('foreign_source') or {}).get('url')}")
        if not host_allowed((r.get("total_source") or {}).get("url", "")):
            errors.append(f"{w}: 総人口の出典が一次ソースでない")
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


def check_population(errors, where, pop):
    """統計の裏付け（自治体×年度連動）の population を検証。"""
    if pop is None:
        return  # 任意項目。無ければスキップ
    for key in ("foreign", "total"):
        v = pop.get(key)
        if not isinstance(v, int) or v <= 0:
            errors.append(f"{where}/population: {key} 不正: {v!r}")
    if not isinstance(pop.get("share_pct"), (int, float)):
        errors.append(f"{where}/population: share_pct 不正")
    if not (pop.get("as_of") or "").strip():
        errors.append(f"{where}/population: 基準日(as_of)が無い")
    if not host_allowed((pop.get("source") or {}).get("url", "")):
        errors.append(f"{where}/population: 統計の出典が一次ソースでない: {(pop.get('source') or {}).get('url')}")


def check_tokyo(errors):
    path = DATA_DIR / "tokyo.json"
    if not path.exists():
        return 0  # best-effort: 未取得なら検証対象外
    data = json.loads(path.read_text(encoding="utf-8"))
    if not host_allowed((data.get("source") or {}).get("url", "")):
        errors.append("tokyo: 出典が一次ソースでない")
    if not (data.get("basis_note") or "").strip():
        errors.append("tokyo: basis_note（集計基準の注記）は必須")
    years = data.get("years") or []
    if not years:
        errors.append("tokyo: 年度が0件")
    n_items = 0
    for y in years:
        yl = y.get("fiscal_year_label") or y.get("fiscal_year")
        items = y.get("items") or []
        if not items:
            errors.append(f"tokyo/{yl}: 事業が0件")
        s = 0
        for it in items:
            n_items += 1
            if not isinstance(it.get("amount_yen"), int) or it["amount_yen"] < 0:
                errors.append(f"tokyo/{yl}/{it.get('name')}: amount_yen 不正")
            # 前年比のある年度のみ増減チェックサム（amount - prev == delta）を再確認
            if it.get("delta_yen") is not None and it.get("amount_yen", 0) - it.get("prev_yen", 0) != it.get("delta_yen"):
                errors.append(f"tokyo/{yl}/{it.get('name')}: 増減チェックサム不一致")
            s += it.get("amount_yen", 0)
        if s != y.get("total_yen"):
            errors.append(f"tokyo/{yl}: total_yen が事業合算と不一致")
        check_population(errors, f"tokyo/{yl}", y.get("population"))
    return n_items


def _check_sk_block(errors, prefix, block, ga_key):
    """埼玉県（prefecture）/ 川口（spotlight）共通の年度ブロック検証。ga_key=一般会計のキー名。"""
    if not block:
        return 0
    if not (block.get("basis_note") or "").strip():
        errors.append(f"{prefix}: basis_note は必須")
    years = block.get("years") or []
    if not years:
        errors.append(f"{prefix}: 年度が0件")
    n = 0
    for y in years:
        yl = y.get("fiscal_year_label") or y.get("fiscal_year")
        if not host_allowed((y.get("source") or {}).get("url", "")):
            errors.append(f"{prefix}/{yl}: 出典が一次ソースでない")
        items = y.get("items") or []
        if not items:
            errors.append(f"{prefix}/{yl}: 事業が0件")
        s = 0
        for it in items:
            n += 1
            if not isinstance(it.get("amount_yen"), int) or it["amount_yen"] < 0:
                errors.append(f"{prefix}/{yl}/{it.get('name')}: amount_yen 不正")
            # 前年比を持つデータ（大阪府等）は増減チェックサムも再確認
            if it.get("delta_yen") is not None and it.get("amount_yen", 0) - it.get("prev_yen", 0) != it.get("delta_yen"):
                errors.append(f"{prefix}/{yl}/{it.get('name')}: 増減チェックサム不一致")
            s += it.get("amount_yen", 0)
        if s != y.get("foreign_total_yen"):
            errors.append(f"{prefix}/{yl}: foreign_total_yen が事業合算と不一致")
        ga = y.get(ga_key)
        if ga and not host_allowed((ga.get("source") or {}).get("url", "")) and ga.get("source"):
            errors.append(f"{prefix}/{yl}: 一般会計の出典が一次ソースでない")
        check_population(errors, f"{prefix}/{yl}", y.get("population"))
    return n


def check_saitama_kawaguchi(errors):
    path = DATA_DIR / "saitama_kawaguchi.json"
    if not path.exists():
        return 0  # best-effort: 未取得なら検証対象外
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    n += _check_sk_block(errors, "saitama_pref", data.get("prefecture"), "general_account")
    n += _check_sk_block(errors, "saitama_kawaguchi", data.get("spotlight"), "city_general_account")
    if n == 0:
        errors.append("saitama_kawaguchi: 県・市ともに公開可能な事業が0件")
    return n


def check_osaka(errors):
    path = DATA_DIR / "osaka.json"
    if not path.exists():
        return 0  # best-effort: 未取得なら検証対象外
    data = json.loads(path.read_text(encoding="utf-8"))
    return _check_sk_block(errors, "osaka", data, "general_account")


# 汎用ビルダー（build_pref.py）出力の都道府県JSON
PREF_FILES = ("hokkaido.json", "miyagi.json", "fukushima.json", "ibaraki.json", "gunma.json", "chiba.json", "niigata.json", "ishikawa.json", "nagano.json", "gifu.json", "shizuoka.json", "aichi.json", "mie.json", "fukuoka.json", "kanagawa.json", "kyoto.json", "hyogo.json", "hiroshima.json", "okayama.json", "ehime.json", "kagawa.json", "kumamoto.json", "okinawa.json", "tochigi.json", "shiga.json", "nara.json", "wakayama.json", "toyama.json", "fukui.json", "aomori.json", "iwate.json", "akita.json", "yamagata.json", "tottori.json", "shimane.json", "yamaguchi.json", "tokushima.json", "kochi.json")


def check_prefs(errors):
    n = 0
    for fn in PREF_FILES:
        path = DATA_DIR / fn
        if not path.exists():
            continue  # best-effort
        data = json.loads(path.read_text(encoding="utf-8"))
        name = fn.replace(".json", "")
        n += _check_sk_block(errors, name, data, "general_account")
        # 事業データの無い年度の一般会計総額（ga_history・任意項目）
        for g in data.get("ga_history") or []:
            w = f"{name}/ga_history/{g.get('fiscal_year_label') or g.get('fiscal_year')}"
            if not isinstance(g.get("amount_yen"), int) or g["amount_yen"] <= 0:
                errors.append(f"{w}: amount_yen 不正: {g.get('amount_yen')!r}")
            if not host_allowed((g.get("source") or {}).get("url", "")):
                errors.append(f"{w}: 出典が一次ソースでない: {(g.get('source') or {}).get('url')}")
    return n


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
    n_osaka = check_osaka(errors)
    n_prefs = check_prefs(errors)
    if errors:
        print("品質ゲート違反:", file=sys.stderr)
        for e in errors:
            print(f"  NG {e}", file=sys.stderr)
        raise SystemExit(1)
    print(
        f"品質ゲート通過: 事業 {n_projects} 件 / 言説 {n_claims} 件 / 比較 {n_comparisons} 組 / 統計 {n_stats} 指標 / 関係予算 {n_budget} 年度 / 用語 {n_glossary} 語 / 東京都 {n_tokyo} 事業 / 埼玉川口 {n_kawaguchi} 事業 / 大阪府 {n_osaka} 事業 / 他県 {n_prefs} 事業、全出典 go.jp/lg.jp等公式",
        file=sys.stderr,
    )


if __name__ == "__main__":
    run()
