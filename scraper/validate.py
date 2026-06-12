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
    path = DATA_DIR / "projects.json"
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
        errors.append("projects.json: amount_note（金額の注記）は必須")
    return len(data["projects"])


def check_claims(errors):
    path = DATA_DIR / "claims.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for c in data["claims"]:
        where = f"claims/{c.get('id', '?')}"
        if c.get("verdict") not in ("true", "false", "conditional"):
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


def run():
    errors = []
    n_projects = check_projects(errors)
    n_claims = check_claims(errors)
    if errors:
        print("品質ゲート違反:", file=sys.stderr)
        for e in errors:
            print(f"  NG {e}", file=sys.stderr)
        raise SystemExit(1)
    print(f"品質ゲート通過: 事業 {n_projects} 件 / 言説 {n_claims} 件、全出典 go.jp/lg.jp", file=sys.stderr)


if __name__ == "__main__":
    run()
