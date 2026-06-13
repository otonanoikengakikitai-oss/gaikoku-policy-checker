"""総合的対応策「関係予算」アダプタ（FY2026の本命データ）

政府が「外国人政策」として束ねた関係予算を、一次ソースの公式PDF/Excelから取得する。
- 令和8年度（FY2026）当初 ＋ 令和7年度補正: 内閣官房 cas.go.jp の公式PDF（施策別・省庁別）
- 令和7年度（FY2025）当初・令和6年度（FY2024）当初: 法務省 moj.go.jp の公式Excel

各文書の「合計」行を正とし、PDFは施策行の合算が合計に一致することを検算（不一致なら公開停止）。

重要な文脈（scope_note）:
  会議体は令和8年1月23日に「外国人材の受入れ・共生」から「外国人の受入れ・秩序ある共生」へ
  改組され、対象範囲が拡大した。FY2026で関係予算が約8.7倍に急増した主因はこの集計範囲の拡大で、
  増分の大半はオーバーツーリズム対策等の観光・インフラ施策（国土交通省主導）である。

依存: pdfplumber, pandas, xlrd（requirements.txt。GitHub Actionsで pip install・無料）。
"""
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

from common import UA

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

DATA_DIR = Path(__file__).resolve().parent.parent / "docs" / "data"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
OUT = DATA_DIR / "policy_budget.json"

COUNCIL_URL = "https://www.cas.go.jp/jp/seisakukaigi/gaikokujinzai/index.html"
FY2026_PDF = "https://www.cas.go.jp/jp/seisaku/symbiotic_society/pdf/sougoutekitaiousaku_yosan.pdf"
# 法務省の過去年度・関連当初予算（Excel）。当初予算額は「予算案」列。
XLS_SOURCES = {
    2025: "https://www.moj.go.jp/isa/content/001433607.xls",
    2024: "https://www.moj.go.jp/isa/content/001413624.xls",
}

SCOPE_NOTE = (
    "会議体は令和8年1月23日に「外国人材の受入れ・共生」から「外国人の受入れ・秩序ある共生」へ改組され、"
    "関係予算の集計範囲が拡大した。FY2026で総額が前年の約8.7倍に急増した主因はこの範囲拡大であり、"
    "増分の大半はオーバーツーリズム対策等の観光・インフラ施策（国土交通省主導）。"
    "在留外国人への給付が同倍率で増えたことを意味しない。"
)


def _download(url, name):
    import ssl
    import urllib.request

    from common import _CTX  # 既存のCA解決済みコンテキストを再利用

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dest = CACHE_DIR / name
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90, context=_CTX) as r:
        dest.write_bytes(r.read())
    return dest


def _amt(s):
    s = (s or "").strip()
    return int(s.replace(",", "")) if re.fullmatch(r"[0-9,]+", s) else None


# 施策名の先頭にある階層記号（（１）, (4), ①, ア , 第１, Ⅰ, １　 等）を除去する
_TITLE_MARKER = re.compile(
    r"^\s*(?:"
    r"[（(][0-9０-９]+[）)]"  # （１） (4)
    r"|[①-⑳]"  # ①〜⑳
    r"|第[0-9０-９]+"  # 第１
    r"|[Ⅰ-ⅩⅠ-Ⅿ]"  # ローマ数字
    r"|[ア-ヶ][\s　]+"  # ア （単独カナ＋空白）
    r"|[0-9０-９]+[\s　\.．、]"  # １　 / 1.
    r")[\s　]*"
)


def clean_title(t):
    t = (t or "").strip()
    prev = None
    while prev != t:  # 入れ子の記号（第１（１）等）も繰り返し除去
        prev = t
        t = _TITLE_MARKER.sub("", t, count=1).strip()
    return t


def _lead_ministry(cell):
    text = (cell or "").replace("\n", "").strip()
    if not text:
        return "その他・複数省庁"
    return re.split(r"[、,・／/]", text)[0].strip() or "その他・複数省庁"


def parse_fy2026_pdf(pdf_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for tbl in page.extract_tables():
                rows.extend(tbl)

    official = None  # (r7補正, r8当初) 千円
    items = []
    current_title = ""  # 直近の階層見出し（施策名に相当）
    for r in rows:
        if len(r) < 6:
            continue
        c0 = re.sub(r"\s+", "", (r[0] or "").strip())
        c1 = (r[1] or "").strip()
        if c0 == "合計":
            official = (_amt(r[2]), _amt(r[3]))
            continue
        # 見出し行（施策番号でなく金額も無い行）は施策名として保持する
        if c0 and not c0.isdigit() and not c1 and _amt(r[2]) is None and _amt(r[3]) is None:
            current_title = clean_title(re.sub(r"\s+", " ", (r[0] or "").replace("\n", "")).strip())
            continue
        v8 = _amt(r[3])
        if v8 is None:
            continue
        items.append(
            {
                "amount_yen": v8 * 1000,
                "ministry": _lead_ministry(r[5]),
                "title": current_title,
                "desc": re.sub(r"\s+", " ", (r[1] or "").replace("\n", " ")).strip(),
            }
        )

    if not official or official[1] is None:
        print("  エラー: FY2026 PDFに公式『合計』行が見つからない", file=sys.stderr)
        raise SystemExit(1)

    r7_supp_yen = (official[0] or 0) * 1000
    r8_total_yen = official[1] * 1000
    items_sum = sum(it["amount_yen"] for it in items)
    if items_sum != r8_total_yen:
        print(
            f"  エラー: FY2026施策合算({items_sum:,})が公式合計({r8_total_yen:,})と不一致。抽出不正の可能性ありで公開停止",
            file=sys.stderr,
        )
        raise SystemExit(1)

    by_min = defaultdict(int)
    for it in items:
        by_min[it["ministry"]] += it["amount_yen"]
    by_ministry = sorted(
        ({"ministry": m, "amount_yen": v} for m, v in by_min.items()),
        key=lambda x: -x["amount_yen"],
    )
    # 全施策を金額順で渡す（最大の施策も必ず含め、合算が総額に一致するようにする）。
    # 説明文は一切省略しない（全文を保持）。説明が空の施策も施策名（見出し）で表示できる。
    top_items = sorted(items, key=lambda x: -x["amount_yen"])

    return {
        "initial_total_yen": r8_total_yen,
        "supplementary_r7_yen": r7_supp_yen,
        "item_count": len(items),
        "by_ministry": by_ministry,
        "top_items": top_items,
        "reconciled": True,
    }


def parse_xls_initial_total(xls_path):
    """法務省Excelの『合計』行から当初予算（『予算案』列）の総額を読む"""
    if pd is None:
        print("  エラー: pandas未導入。requirements.txtの依存を入れること", file=sys.stderr)
        raise SystemExit(1)
    df = pd.ExcelFile(xls_path).parse(0, header=None, dtype=str)
    # ヘッダ行（『施策番号』を含む行）を起点に、当初予算（『予算案』を含み『補正』でない）列を特定する。
    # 先頭のタイトル行にも「…予算案について」と含まれるため、列名だけの探索だと誤検出する。
    def norm(c):
        return re.sub(r"\s+", "", c) if isinstance(c, str) else ""

    header_row = None
    for i in range(min(12, len(df))):
        if any("施策番号" in norm(c) for c in df.iloc[i].tolist()):
            header_row = i
            break
    budget_col = None
    if header_row is not None:
        for j, cell in enumerate(df.iloc[header_row].tolist()):
            n = norm(cell)
            if "予算案" in n and "補正" not in n:
                budget_col = j
                break
    if budget_col is None:
        print(f"  エラー: {xls_path.name} のヘッダ行に当初予算（予算案）列が見つからない", file=sys.stderr)
        raise SystemExit(1)
    for i in range(len(df)):
        if str(df.iloc[i, 0]).strip() == "合計":
            val = _amt(str(df.iloc[i, budget_col]))
            if val is None:
                break
            return val * 1000
    print(f"  エラー: {xls_path.name} に当初予算の『合計』行が見つからない", file=sys.stderr)
    raise SystemExit(1)


def run():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("総合的対応策 関係予算（FY2026本命）を取得中…", file=sys.stderr)

    pdf_path = _download(FY2026_PDF, "taiousaku_fy2026.pdf")
    fy2026 = parse_fy2026_pdf(pdf_path)
    print(
        f"  FY2026当初: {fy2026['initial_total_yen']/1e8:,.1f}億円（{fy2026['item_count']}施策・検算一致）"
        f" / R7補正: {fy2026['supplementary_r7_yen']/1e8:,.1f}億円",
        file=sys.stderr,
    )

    series = [
        {
            "year": 2026,
            "label": "令和8年度当初",
            "amount_yen": fy2026["initial_total_yen"],
            "source": {"label": "内閣官房 総合的対応策関連 R8当初予算（PDF）", "url": FY2026_PDF},
        }
    ]
    for year, url in XLS_SOURCES.items():
        path = _download(url, f"taiousaku_{year}.xls")
        total = parse_xls_initial_total(path)
        series.append(
            {
                "year": year,
                "label": f"令和{year - 2018}年度当初",
                "amount_yen": total,
                "source": {"label": f"法務省 総合的対応策関連 令和{year - 2018}年度当初予算（Excel）", "url": url},
            }
        )
        print(f"  FY{year}当初: {total/1e8:,.1f}億円", file=sys.stderr)
    series.sort(key=lambda s: s["year"])

    prev = next((s for s in series if s["year"] == 2025), None)
    cur = next((s for s in series if s["year"] == 2026), None)
    yoy = None
    if prev and cur and prev["amount_yen"]:
        delta = cur["amount_yen"] - prev["amount_yen"]
        yoy = {
            "from_year": 2025,
            "to_year": 2026,
            "delta_yen": delta,
            "pct": round(delta / prev["amount_yen"] * 100, 1),
        }

    out = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "title": "外国人の受入れ・秩序ある共生のための総合的対応策 関係予算",
        "basis_note": "政府が総合的対応策の関連施策として束ねた関係予算（当初予算ベース）。行政事業レビューの事業別予算とは集計基準が異なる。",
        "scope_note": SCOPE_NOTE,
        "primary_source": {"label": "内閣官房 外国人の受入れ・秩序ある共生社会実現に関する関係閣僚会議", "url": COUNCIL_URL},
        "initial_budget_series": series,
        "yoy_2025_2026": yoy,
        "fy2026": fy2026,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"関係予算 3カ年＋FY2026施策内訳 → {OUT}", file=sys.stderr)
    return out


if __name__ == "__main__":
    run()
