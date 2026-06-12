"""全パイプライン実行: 収集 → 言説検証 → 品質ゲート"""
import argparse

import build_claims
import rs_system
import validate

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--use-cache", action="store_true")
    args = ap.parse_args()
    rs_system.run(year=args.year, use_cache=args.use_cache)
    build_claims.run()
    validate.run()
