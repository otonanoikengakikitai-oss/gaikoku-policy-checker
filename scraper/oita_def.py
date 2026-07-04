"""大分県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第九波（47都道府県コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "大分県"
OUT_NAME = "oita.json"

_DOCS = {
    "ICHIRAN": {"label": "大分県 令和8年度一般会計当初予算案（事業別一覧）", "url": "https://www.pref.oita.jp/uploaded/attachment/2261421.pdf"},
    "GIAN": {"label": "大分県 令和8年度一般会計・特別会計議案", "url": "https://www.pref.oita.jp/uploaded/attachment/2261050.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["ICHIRAN"],
        "items": [
            _item('外国人労働者受入対策強化事業', '外国人労働者受入対策強化事', 'ICHIRAN', '外国人材', '商工観光労働部 産業人材政策課', 63152000, '63,15263,947',
                  '企業向け外国人材雇用相談窓口の運営（おおいたジョブステーション内）、就業環境整備・日本語教育・技能習得支援への助成（前年度63,947千円が資料に併記）。'),
            _item('多文化共生推進事業', '多文化共生推進事業', 'ICHIRAN', '多文化共生', '企画振興部 国際政策課', 57973000, '多文化共生推進事業57,97343,939',
                  '「外国人共生コーディネーター」の振興局配置（5人）・相談対応等（前年度43,939千円が資料に併記・32%増）。'),
        ],
        "general_account": {
            "amount_yen": 730058000000,
            "amount_label": "7,300億5,800万円",
            "evidence": '歳入歳出それぞれ730,058,000千円と定める',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GIAN"],
        },
    },
]

BASIS_NOTE = (
    '大分県の外国人特化予算（「一般会計当初予算案（事業別一覧）」に事業名・当年+前年額・所管課が明記され、連結証跡で検証を通過した外国人特化事業2件）。一般会計総額は当初予算議案第1条の法定条文。令和5〜7年度は追加調査で拡張予定のため未収録。金額は千円単位。'
)
TREND_NOTE = (
    '大分県の外国人特化予算（令和8年度・確認可能分）は約1.2億円で、外国人労働者受入対策（6,315万円）と多文化共生推進（5,797万円・前年比+32%＝外国人共生コーディネーター配置）が二本柱。県一般会計（7,301億円）の約0.017%であり、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
