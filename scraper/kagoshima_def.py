"""鹿児島県の外国人特化予算の定義 — キュレーション方式（汎用 build_pref.py 用）

第九波（47都道府県コンプリート）で追加。一次ソース・収録範囲は BASIS_NOTE を参照。
"""

GOVERNMENT = "鹿児島県"
OUT_NAME = "kagoshima.json"

_DOCS = {
    "GAIYO": {"label": "鹿児島県 令和8年度当初予算（案）の概要", "url": "https://www.pref.kagoshima.jp/ab05/kensei/zaisei/yosan/r7/documents/126340_20260209144559-1.pdf"},
}


def _item(name, name_ev, dockey, cat, bureau, yen, ev, desc):
    return {"name": name, "name_evidence": name_ev, "doc": _DOCS[dockey]["url"], "doc_type": "pdf",
            "category": cat, "bureau": bureau, "amount_yen": yen, "amount_evidence": ev, "desc": desc}


YEARS = [
    {
        "fiscal_year": 2025,
        "fiscal_year_label": "令和7年度",
        "source": _DOCS["GAIYO"],
        "items": [],
        "empty_note": '※令和7年度は主要資料に外国人特化事業の記載（金額明記）が確認できないため事業は未収録（一般会計総額のみ収録）。',
        "general_account": {
            "amount_yen": 852734000000,
            "amount_label": "8,527億3,400万円",
            "evidence": '一般会計920,724852,734108.0',
            "label": "令和7年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
    {
        "fiscal_year": 2026,
        "fiscal_year_label": "令和8年度",
        "source": _DOCS["GAIYO"],
        "items": [
            _item('外国人材確保総合支援事業', '外国人材確保総合支援事業', 'GAIYO', '外国人材', '外国人材政策推進課', 23535000, '外国人材確保総合支援事業23,535',
                  '「外国人材から選ばれるかごしま」に向けた確保から定着までの総合支援（外国人材のための「かごしま」理解促進等）。'),
            _item('多文化共生の地域づくり事業', '多文化共生の地', 'GAIYO', '多文化共生', 'くらし共生協働課', 2057000, '日本人と外国人が共に学ぶワークショッ2,057',
                  '地域住民の多文化共生の意識醸成・日本人と外国人が共に学ぶワークショップ等をモデル実施する市町村への支援。'),
        ],
        "general_account": {
            "amount_yen": 920724000000,
            "amount_label": "9,207億2,400万円",
            "evidence": '一般会計920,724852,734108.0',
            "label": "令和8年度 一般会計 当初予算",
            "source": _DOCS["GAIYO"],
        },
    },
]

BASIS_NOTE = (
    '鹿児島県の外国人特化予算（「当初予算（案）の概要」に事業名と金額が明記され、連結証跡で検証を通過した外国人特化事業2件）。観光注意喚起等は含まない。一般会計総額は「920,724（R8）852,734（R7）108.0%」の前年併記連結（百万円）。令和5〜7年度は追加調査で拡張予定のため未収録。金額は千円単位。'
)
TREND_NOTE = (
    '鹿児島県の外国人特化予算（令和8年度・確認可能分）は約2,600万円で、外国人材政策推進課による確保総合支援（2,354万円）が中心。県一般会計（9,207億円）の約0.003%であり、『莫大な税金で外国人を優遇』という言説と実際の予算スケールには歴然とした差がある。'
)
