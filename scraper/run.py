"""全パイプライン実行: 収集 → 比較組み立て → 統計 → 関係予算 → 言説検証 → 品質ゲート

耐障害設計: 各データ源（rssystem.go.jp / cas.go.jp / e-Stat 等）が一時的に
到達不能・ブロックされても、そのアダプタはスキップして既存の確定データ（コミット済みJSON）を
保持したまま続行する。最後に validate.py を必ず厳格実行し、公開されるデータが常に
品質ゲートを満たすことを保証する（壊れたデータは公開されない）。
"""
import argparse
import sys

import build_claims
import build_comparisons
import build_saitama_kawaguchi
import build_tokyo
import rs_system
import stats
import taiousaku
import validate


def safe(name, fn):
    """データ源の取得・整合性検証の失敗を許容し、既存の確定データを保持して続行する。
    アダプタは整合性チェック通過後にのみファイルを書き出すため、失敗時は旧データが保たれる。
    最終の validate.py が公開データ全体を厳格に再検証する。"""
    try:
        fn()
    except (Exception, SystemExit) as e:  # noqa: BLE001 — 取得/解析/整合性失敗を握り既存データを維持
        print(f"  警告: {name} をスキップ（既存の確定データを保持）: {e}", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=str, default=None, help="カンマ区切り（例: 2024,2025）。省略時はAPIの最新3年度")
    ap.add_argument("--use-cache", action="store_true")
    args = ap.parse_args()
    years = [int(y) for y in args.years.split(",")] if args.years else None

    safe("rs_system（行政事業レビュー）", lambda: rs_system.run(years=years, use_cache=args.use_cache))
    safe("build_comparisons（ならべて比較）", build_comparisons.run)
    safe("stats（e-Stat / ISA最新実績）", stats.run)
    safe("taiousaku（関係予算）", taiousaku.run)
    safe("build_tokyo（東京都）", build_tokyo.run)
    safe("build_saitama_kawaguchi（埼玉・川口）", build_saitama_kawaguchi.run)
    safe("build_claims（言説）", build_claims.run)
    # 品質ゲートは必ず厳格実行（既存＋新規データの全件検証）。違反があれば exit 1 で公開を止める。
    validate.run()
