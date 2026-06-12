"""e-Stat統計ダッシュボードAPI（APIキー不要）アダプタ

https://dashboard.e-stat.go.jp/ の公開JSON APIから、言説検証の文脈となる
基礎統計（在留外国人数・総人口）の全国時系列を取得する。
指標コードと指標名はAPIメタデータで毎回照合し、不一致なら公開しない。
"""
import datetime
import json
import sys
import urllib.parse
from pathlib import Path

from common import http_get_json

DASH = "https://dashboard.e-stat.go.jp/api/1.0/Json"
OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "stats.json"

INDICATORS = [
    {"key": "zairyu_total", "code": "0201120001000010000", "name": "在留外国人数", "unit": "人"},
    {"key": "population_total", "code": "0201010000000010000", "name": "総人口（総数）", "unit": "人"},
]


def verify_indicator_name(code, expected_name):
    q = urllib.parse.quote(expected_name)
    data = http_get_json(f"{DASH}/getIndicatorInfo?Lang=JP&SearchIndicatorWord={q}")
    objs = data["GET_META_INDICATOR_INF"]["METADATA_INF"]["CLASS_INF"]["CLASS_OBJ"]
    if isinstance(objs, dict):
        objs = [objs]
    return any(o.get("@code") == code and o.get("@name") == expected_name for o in objs)


def fetch_national_series(code):
    data = http_get_json(f"{DASH}/getData?Lang=JP&IndicatorCode={code}")
    rows = data["GET_STATS"]["STATISTICAL_DATA"]["DATA_INF"]["DATA_OBJ"]
    dedup = {}
    for r in rows:
        v = r["VALUE"]
        if v.get("@regionCode") != "00000":
            continue
        t = v.get("@time", "")
        if not t[:4].isdigit():
            continue
        dedup[int(t[:4])] = int(v["$"])
    return [{"year": y, "value": val} for y, val in sorted(dedup.items())]


def run():
    indicators = {}
    for ind in INDICATORS:
        if not verify_indicator_name(ind["code"], ind["name"]):
            print(f"  エラー: 指標 {ind['code']} の名称が想定（{ind['name']}）と不一致。公開中止", file=sys.stderr)
            raise SystemExit(1)
        series = fetch_national_series(ind["code"])
        if not series:
            print(f"  エラー: 指標 {ind['name']} の全国系列が空", file=sys.stderr)
            raise SystemExit(1)
        indicators[ind["key"]] = {
            "name": ind["name"],
            "unit": ind["unit"],
            "indicator_code": ind["code"],
            "series": series,
            "latest": series[-1],
        }
        print(f"  {ind['name']}: {series[-1]['year']}年 {series[-1]['value']:,}{ind['unit']}（{len(series)}年分）", file=sys.stderr)

    derived = {}
    z = {s["year"]: s["value"] for s in indicators["zairyu_total"]["series"]}
    p = {s["year"]: s["value"] for s in indicators["population_total"]["series"]}
    common_years = sorted(set(z) & set(p))
    if common_years:
        y = common_years[-1]
        derived["zairyu_share_pct"] = {
            "year": y,
            "value": round(z[y] / p[y] * 100, 2),
            "note": "在留外国人数 ÷ 総人口（同一年で算出）",
        }

    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "name": "e-Stat 統計ダッシュボード（政府統計の総合窓口）",
            "url": "https://dashboard.e-stat.go.jp/",
            "stat_name": "社会・人口統計体系ほか（出典統計はダッシュボード上で確認可能）",
        },
        "indicators": indicators,
        "derived": derived,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"統計 {len(indicators)} 指標 → {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
