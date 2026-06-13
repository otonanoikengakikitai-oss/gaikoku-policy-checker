"""e-Stat統計ダッシュボードAPI（APIキー不要）アダプタ

https://dashboard.e-stat.go.jp/ の公開JSON APIから、言説検証の文脈となる
基礎統計（在留外国人数・総人口）の全国時系列を取得する。
指標コードと指標名はAPIメタデータで毎回照合し、不一致なら公開しない。
"""
import datetime
import json
import re
import sys
import urllib.parse
from pathlib import Path

from common import http_get_json, http_get_raw

DASH = "https://dashboard.e-stat.go.jp/api/1.0/Json"
OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "stats.json"

INDICATORS = [
    {"key": "zairyu_total", "code": "0201120001000010000", "name": "在留外国人数", "unit": "人"},
    {"key": "population_total", "code": "0201010000000010000", "name": "総人口（総数）", "unit": "人"},
]

# 出入国在留管理庁の「在留外国人数について」プレスリリース（一次ソース）の探索範囲。
# e-Statダッシュボードの年次値より新しい最新実績（半期ごと）をここから動的に取得する。
ISA_PRESS = "https://www.moj.go.jp/isa/publications/press/13_{:05d}.html"
ISA_PROBE_RANGE = range(60, 75)  # 既知: 13_00062=令和7年末。前方を探索し新リリースを自動追従


def _parse_jp_number(s):
    """『412万5,395』『3,956,619』等を整数に変換"""
    s = s.replace(",", "").replace("，", "").translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    m = re.match(r"^(\d+)万(\d+)$", s)
    if m:
        return int(m.group(1)) * 10000 + int(m.group(2))
    m = re.match(r"^(\d+)万$", s)
    if m:
        return int(m.group(1)) * 10000
    return int(s) if s.isdigit() else None


def fetch_latest_isa_residents():
    """ISAプレスから最新の在留外国人数（基準日つき確定値）を動的取得する。
    捏造防止のため、実在・公開済みのページに記載された数値のみを採用する。"""
    best = None
    for n in ISA_PROBE_RANGE:
        url = ISA_PRESS.format(n)
        raw = http_get_raw(url)
        if not raw:
            continue
        tm = re.search(r"<title>(.*?)</title>", raw, re.S)
        title = re.sub(r"\s+", "", tm.group(1)) if tm else ""
        if "在留外国人数について" not in title:
            continue
        # 基準日: 令和N年末 / 令和N年6月末
        pm = re.search(r"令和(\d+)年(6月末|６月末|末)現在", title.replace("６", "6"))
        if not pm:
            continue
        reiwa = int(pm.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789")))
        is_yearend = pm.group(2) == "末"
        year = 2018 + reiwa
        month = 12 if is_yearend else 6
        body = re.sub(r"\s+", "", re.sub(r"<[^>]+>", " ", raw))
        vm = re.search(r"在留外国人数は[、，]([0-9０-９,，万]+)人", body)
        if not vm:
            continue
        value = _parse_jp_number(vm.group(1))
        if value is None:
            continue
        ym = re.search(r"前年(?:末|同期)比([0-9０-９,，万]+)人[、，]([0-9０-９.．]+)[%％]増", body)
        yoy_abs = _parse_jp_number(ym.group(1)) if ym else None
        yoy_pct = float(ym.group(2).translate(str.maketrans("０１２３４５６７８９．", "0123456789."))) if ym else None
        rec = {
            "value": value,
            "year": year,
            "month": month,
            "as_of": f"令和{reiwa}年{'末' if is_yearend else '6月末'}（{year}年{month}月末）現在",
            "yoy_abs": yoy_abs,
            "yoy_pct": yoy_pct,
            "source": {"label": "出入国在留管理庁 在留外国人数について", "url": url},
        }
        if best is None or (rec["year"], rec["month"]) > (best["year"], best["month"]):
            best = rec
    return best


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

    # ダッシュボードの年次値より新しい最新実績（ISAプレスの半期値）を動的取得
    print("  出入国在留管理庁プレスから最新実績を探索中…", file=sys.stderr)
    latest_actual = fetch_latest_isa_residents()
    if latest_actual:
        print(
            f"  最新実績: {latest_actual['as_of']} {latest_actual['value']:,}人（{latest_actual['source']['url']}）",
            file=sys.stderr,
        )
    else:
        print("  注意: ISAプレスから最新実績を取得できず（ダッシュボードの年次値のみ公開）", file=sys.stderr)
    indicators["zairyu_total"]["latest_actual"] = latest_actual

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
