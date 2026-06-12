"""全パイプライン実行: 収集 → 比較組み立て → 統計 → 言説検証 → 品質ゲート"""
import argparse

import build_claims
import build_comparisons
import rs_system
import stats
import validate

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=str, default=None, help="カンマ区切り（例: 2024,2025）。省略時はAPIの最新3年度")
    ap.add_argument("--use-cache", action="store_true")
    args = ap.parse_args()
    rs_system.run(years=[int(y) for y in args.years.split(",")] if args.years else None, use_cache=args.use_cache)
    build_comparisons.run()
    stats.run()
    build_claims.run()
    validate.run()
