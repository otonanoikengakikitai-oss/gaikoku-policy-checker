"""claims_def.py の言説定義を検証し docs/data/claims.json を生成する

- 出典URLのドメインが go.jp / lg.jp 以外なら即エラー（公開させない）
- 出典URLの生存確認に失敗した言説は published=false として除外
"""
import datetime
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from claims_def import CLAIMS
from common import url_alive

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "claims.json"
ALLOWED_SUFFIXES = (".go.jp", ".lg.jp")
VERDICTS = {"true", "false", "conditional"}


def host_allowed(url):
    host = urlparse(url).hostname or ""
    return host.endswith(ALLOWED_SUFFIXES)


def run():
    published, errors = [], []
    for c in CLAIMS:
        if c["verdict"] not in VERDICTS:
            errors.append(f"{c['id']}: 不正なverdict {c['verdict']!r}")
            continue
        bad = [s["url"] for s in c["sources"] if not host_allowed(s["url"])]
        if bad:
            errors.append(f"{c['id']}: 一次ソース以外のドメイン {bad}")
            continue
        dead = [s["url"] for s in c["sources"] if not url_alive(s["url"])]
        if dead:
            print(f"  警告: {c['id']} の出典が応答せず非公開にする: {dead}", file=sys.stderr)
            continue
        published.append({**c, "checked_at": datetime.date.today().isoformat()})
    if errors:
        for e in errors:
            print(f"  エラー: {e}", file=sys.stderr)
        raise SystemExit(1)
    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "claims": published,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"言説 {len(published)}/{len(CLAIMS)} 件を公開 → {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
